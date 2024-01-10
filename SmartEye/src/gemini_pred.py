import os
import json
import base64
import sys
import pathlib
import sqlite3
import google

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import google.generativeai as genai

import base64
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
from dotenv import load_dotenv
from utils import *
import chromadb
from datetime import datetime
from messanger import *

# Load environment variables from the .env file
load_dotenv()

# Access the API key using the environment variable
api_key = os.getenv("API_KEY")

PROJECT_ID = "gen-lang-client-0244575719"  # @param {type:"string"} # hackthon-409604
LOCATION = "us-central1"  # @param {type:"string"}
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Configure API key (replace with your actual key)
genai.configure(api_key=api_key)

# Get the directory of the current script or module
current_dir = os.path.dirname(os.path.abspath(__file__))
PARENT_dIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)

client = chromadb.PersistentClient(path=PARENT_dIR)
collection = client.get_or_create_collection(
    name="smarteye",
    # metadata={"hnsw:space": "cosine"} # l2 is the default
)  # Get a collection object from an existing collection, by name. If it doesn't exist, create it.

# Connect to the database
db_path = os.path.join(PARENT_dIR, "current_alerts.db")
model = GenerativeModel("gemini-pro-vision")


def fetch_prompt():
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Fetch data from the database
    cursor.execute("SELECT Name, Description FROM current_alerts WHERE Active = 1")
    result = cursor.fetchall()

    # Close the database connection
    connection.close()

    base_prompt = """
    Based on the video identify the alerts name based on the description below  

    Alert Name : Description
    ------------------------
    """

    # Process the results
    if result:
        # Create a string with the desired format
        result_string = "\n".join(
            [f"{name} : {description}" for name, description in result]
        )

    close_prompt = """\n\nif No alert situation occured then send as 'No Alert'. 

    Provide the answer JSON format below
    {
        "AlertName": <comma seperated alerts names based on the list provided>,
        "Summary": <Provide complete details happened from the video along with details of various objects present. Also include audio summary>,
        "Objects" : <comma seperated of all the objects>
    }
    """

    PROMPT = base_prompt + result_string + close_prompt

    print(f"Complete PROMPT: {PROMPT}\n\n")
    return PROMPT


def video_processing(rel_video_path):
    video_path = os.path.join(PARENT_dIR, rel_video_path)
    video_chunks_path = split_video_into_chunks(video_path)
    prompt = fetch_prompt()

    for chunk_path in video_chunks_path:
        # Read the encoded video as bytes
        with open(chunk_path, "rb") as video_file:
            video_bytes = video_file.read()

        # Convert the bytes to Base64
        base64_encoded = base64.b64encode(video_bytes).decode("utf-8")

        responses = model.generate_content(
            [
                Part.from_data(
                    data=base64.b64decode(base64_encoded), mime_type="video/mp4"
                ),
                prompt,
            ],
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.4,
                "top_p": 1,
                "top_k": 32,
            },
            # stream=True,
        )

        response = responses.text
        json_response = json.loads(response)

        if json_response["AlertName"] == "No Alert":
            json_response["AlertName"] = ""
        alert_name = json_response["AlertName"]

        json_response["VideoChunkPath"] = chunk_path
        json_response["SourceVideoPath"] = video_path

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        json_response["Timestamp"] = timestamp
        collection.add(
            documents=[json_response["Summary"]],
            metadatas=[
                {
                    "VideoChunkPath": json_response["VideoChunkPath"],
                    "SourceVideoPath": json_response["SourceVideoPath"],
                    "AlertName": alert_name,
                    "Timestamp": timestamp,
                },
            ],
            ids=[str(create_database_and_fetch_latest_id() + 1)],
        )

        insert_data_into_table(json_response)
        if alert_name:
            send_alert_notification(alert_name, json_response["Summary"], chunk_path)

        os.makedirs(chunk_path.replace("processing", "processed"), exist_ok=True)
        shutil.move(chunk_path, chunk_path.replace("processing", "processed"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 gemini_pred.py <video_file_path>")
        sys.exit(1)

    video_file_path = sys.argv[1]
    video_processing(video_file_path)
