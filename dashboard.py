import os

import pandas as pd
import pg8000.dbapi
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME", "postgres")

if not DB_PASSWORD:
    raise RuntimeError("DB_PASSWORD ist nicht gesetzt.")

st.set_page_config(page_title="SBB Abfahrten", layout="wide")


@st.cache_data(ttl=60)
def load_data():
    connection = pg8000.dbapi.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        database=DB_NAME,
    )
    query = """
        SELECT station_name, departure_time, train_category, train_number,
               destination, delay_minutes
        FROM departures
        ORDER BY departure_time DESC
    """
    dataframe = pd.read_sql(query, connection)
    connection.close()

    dataframe["departure_time"] = pd.to_datetime(dataframe["departure_time"])
    dataframe["hour_of_day"] = dataframe["departure_time"].dt.hour
    dataframe["is_delayed"] = dataframe["delay_minutes"] > 0
    return dataframe


try:
    dataframe = load_data()

    st.title("Abfahrten ab Zürich HB")
    st.caption("Aktuelle Einträge aus der Datenbank")

    overview_tab, destinations_tab, details_tab = st.tabs(
        ["Übersicht", "Ziele", "Details"]
    )

    with overview_tab:
        st.header("Übersicht")
        first, second, third = st.columns(3)
        first.metric("Abfahrten", len(dataframe))
        second.metric(
            "Letzte Abfahrt",
            (
                dataframe["departure_time"].max().strftime("%d.%m.%Y %H:%M")
                if not dataframe.empty
                else "Keine Daten"
            ),
        )
        third.metric(
            "Verspätete Abfahrten",
            int(dataframe["is_delayed"].sum()),
        )

        st.dataframe(
            dataframe[
                [
                    "station_name",
                    "departure_time",
                    "train_category",
                    "destination",
                    "delay_minutes",
                ]
            ].head(100),
            use_container_width=True,
        )

    with destinations_tab:
        st.header("Verspätungen nach Ziel")

        if dataframe.empty:
            st.info("Keine Daten vorhanden.")
        else:
            destination_data = (
                dataframe.groupby("destination")
                .agg(
                    departures=("train_number", "count"),
                    average_delay=("delay_minutes", "mean"),
                )
                .reset_index()
                .sort_values("average_delay", ascending=False)
                .head(10)
            )
            chart = px.bar(
                destination_data,
                x="destination",
                y="average_delay",
                title="Durchschnittliche Verspätung",
                labels={
                    "average_delay": "Verspätung in Minuten",
                    "destination": "Ziel",
                },
            )
            st.plotly_chart(chart, use_container_width=True)

    with details_tab:
        st.header("Weitere Angaben")
        st.dataframe(
            dataframe[
                ["departure_time", "train_category", "train_number",
                 "destination", "delay_minutes", "hour_of_day"]
            ].head(100),
            use_container_width=True,
        )
except Exception as error:
    st.error(f"Die Daten konnten nicht geladen werden: {error}")
