import os

import pg8000.dbapi


DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_NAME = os.environ.get("DB_NAME", "postgres")

try:
    print("Verbinde mit der Datenbank...")
    connection = pg8000.dbapi.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    connection.autocommit = True
    cursor = connection.cursor()

    with open("schema.sql", "r", encoding="utf-8") as file:
        cursor.execute(file.read())

    print("Die Tabelle departures ist verfügbar.")
    cursor.close()
    connection.close()
except Exception as error:
    print(f"Fehler bei der Einrichtung der Datenbank: {error}")
