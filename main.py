import json
import os
import urllib.request
from datetime import datetime

import boto3
import pg8000.dbapi


DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ.get("DB_USER", "postgres")
DB_NAME = os.environ.get("DB_NAME", "postgres")
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
API_URL = os.environ.get(
    "API_URL",
    "https://transport.opendata.ch/v1/stationboard?station=Zurich&limit=50",
)
TMP_FILE = "/tmp/sbb_data.json"

ssm = boto3.client("ssm")


def get_db_password():
    response = ssm.get_parameter(Name="/sbb/db_password", WithDecryption=True)
    return response["Parameter"]["Value"]


def lambda_handler(event, context):
    try:
        request = urllib.request.Request(
            API_URL,
            headers={"User-Agent": "sbb-aws-pipeline/1.0"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        with open(TMP_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        s3_key = f"zurich_hb_{timestamp}.json"
        boto3.client("s3").upload_file(TMP_FILE, S3_BUCKET_NAME, s3_key)

        connection = pg8000.dbapi.connect(
            user=DB_USER,
            password=get_db_password(),
            host=DB_HOST,
            database=DB_NAME,
        )
        cursor = connection.cursor()
        insert_query = """
            INSERT INTO departures
                (station_name, departure_time, train_category, train_number,
                 destination, delay_minutes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        count = 0
        for item in data.get("stationboard", []):
            stop = item.get("stop", {})
            delay = int(stop["delay"]) if stop.get("delay") else 0
            cursor.execute(
                insert_query,
                (
                    "Zürich HB",
                    stop["departure"],
                    item.get("category", ""),
                    item.get("number", ""),
                    item.get("to", ""),
                    delay,
                ),
            )
            count += 1

        connection.commit()
        cursor.close()
        connection.close()

        return {
            "statusCode": 200,
            "body": f"Erfolg! S3 Upload: {s3_key}. RDS Inserts: {count} Fahrten gespeichert.",
        }
    except Exception as error:
        print(f"Fehler: {error}")
        return {"statusCode": 500, "body": str(error)}
    finally:
        if os.path.exists(TMP_FILE):
            os.remove(TMP_FILE)
