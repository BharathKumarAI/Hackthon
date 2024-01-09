import sqlite3
import json
from datetime import datetime
from collections import Counter
from database_utils import *
from messanger import * 

def check_for_duplicates_and_create_custom_alert():
    # Connect to SQLite database (create if not exists)
    conn = sqlite3.connect('guidinglight.db')

    with conn:
        cursor = conn.cursor()
        # Fetch the last 5 entries from the database
        cursor.execute('''
            SELECT * FROM guidinglight WHERE mode != "Custom" AND alert != "Abandoned Item" ORDER BY id DESC LIMIT 5
        ''')
        entries = cursor.fetchall()

        # Extract objects from each entry
        all_objects = []
        for entry in entries:
            print(f"Objects in entry {entry[0]}: {entry[5]}")
            objects_data = entry[5]
            try:
                # Try loading as JSON
                objects_list = json.loads(objects_data)
                print(f"Parsed as JSON: {objects_list}")
                # Strip white spaces from each object
                all_objects.extend(obj.strip() for obj in objects_list)
            except json.decoder.JSONDecodeError:
                # If loading as JSON fails, assume it's a string and split
                print("Parsing as JSON failed. Assuming it's a string.")
                # Strip white spaces from each object
                all_objects.extend(obj.strip() for obj in objects_data.lower().split(','))

        # Check for duplicates across the last 5 entries
        common_objects = [obj for obj, count in Counter(all_objects).items() if count == 5]
        common_objects = [obj for obj in common_objects if obj.lower() != 'person']

        if common_objects:
            print("Common objects found are : " + ", ".join(common_objects))
            
            # Check if there are still common objects after excluding "person"
            if common_objects:
                common_objects_str = ', '.join(common_objects)
                # Create a custom alert
                custom_alert = {
                    "Mode": "Custom",
                    "Alert": "Abandoned item",
                    "Description": f"{common_objects_str} are abandoned items",
                    "Objects": common_objects_str,
                    "Distance": -1,
                    "latitude": entries[0][7],  # Latitude from the most recent entry
                    "longitude": entries[0][8],  # Longitude from the most recent entry
                    "image_path": ', '.join(entry[9] for entry in entries)  # Combine image paths
                }

                # Save the custom alert to the database
                save_to_database(custom_alert)

                # Send notification to Telegram
                send_alert_notification(custom_alert["Alert"], custom_alert["latitude"], custom_alert["longitude"], custom_alert["image_path"])
        else:
            print("No common objects found")

if __name__ == "__main__":
    check_for_duplicates_and_create_custom_alert()
