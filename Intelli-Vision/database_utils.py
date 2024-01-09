import sqlite3
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

def create_database():
    # Connect to SQLite database (create if not exists)
    conn = sqlite3.connect('guidinglight.db')

    # Create a table if not exists
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS guidinglight (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                mode TEXT,
                alert TEXT,
                description TEXT,
                objects TEXT,
                distance REAL,
                latitude REAL,
                longitude REAL,
                image_path TEXT
            )
        ''')
    conn.close()

# Convert JSON to a tuple for insertion
def save_to_database(json_response):
    # Connect to SQLite database (create if not exists)
    conn = sqlite3.connect('guidinglight.db')

    # Define the keys you expect in the JSON response
    expected_keys = ["Mode", "Alert", "Description", "Objects", "Distance", "latitude", "longitude", "image_path"]

    # Replace "None" with an empty string for the "Alert" key
    json_response["Alert"] = json_response.get("Alert", "")
    if json_response["Alert"] == "None":
        json_response["Alert"] = ""

    # Fill missing keys with empty values
    for key in expected_keys:
        if key not in json_response:
            json_response[key] = ""

    # Include timestamp
    json_response["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    data_tuple = (
        json_response["timestamp"],
        json_response["Mode"],
        json_response["Alert"],
        json_response["Description"],
        json_response["Objects"],
        json_response["Distance"],
        json_response["latitude"],
        json_response["longitude"],
        json_response["image_path"]
    )

    # Insert data into the table
    with conn:
        conn.execute('''
            INSERT INTO guidinglight (timestamp, mode, alert, description, objects, distance, latitude, longitude, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data_tuple)
    conn.close()

# Function to retrieve the last entries from the database
def get_last_entries(limit=5):
    # Connect to SQLite database (create if not exists)
    conn = sqlite3.connect('guidinglight.db')

    with conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT * FROM guidinglight ORDER BY id DESC LIMIT {limit}
        ''')
        return cursor.fetchall()

# Close the connection (optional, depending on how you manage the connection lifecycle)
# conn.close()