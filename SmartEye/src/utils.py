import base64
import os
import uuid
import io
import re
import cv2
import shutil

from langchain_core.messages import HumanMessage
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatVertexAI
from langchain_community.llms import VertexAI
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
import sqlite3
from sqlite3 import OperationalError

from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import InMemoryStore
from langchain_community.embeddings import VertexAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from PIL import Image
from datetime import datetime

# Get the directory of the currently executing script
current_dir = os.path.dirname(os.path.abspath(__file__))
PARENT_dIR = os.path.abspath(os.path.join(current_dir, os.pardir))


from moviepy.editor import VideoFileClip
from time import sleep


def split_video_into_chunks(source_file_path, chunk_duration_sec=20):
    video_folder = os.path.dirname(source_file_path)
    print(video_folder)
    video_file_name = source_file_path.split("/")[-1]
    file_name = video_file_name.split(".")[0]

    processing_dir = os.path.join(video_folder, "processing")
    chunks_dir = os.path.join(processing_dir, "chunks")

    print(processing_dir)
    os.makedirs(processing_dir, exist_ok=True)
    os.makedirs(chunks_dir, exist_ok=True)

    shutil.move(source_file_path, processing_dir)
    processing_file_path = os.path.join(processing_dir, video_file_name)

    current_duration = VideoFileClip(processing_file_path).duration
    print("Current Duration of the file: " + str(current_duration) + " in sec")
    full_duration = current_duration

    chunks_path = []
    current_video = os.path.join(
        chunks_dir, f"{file_name}_{str(current_duration).replace('.','_')}.mp4"
    )

    try:
        while current_duration > chunk_duration_sec:
            clip = VideoFileClip(processing_file_path).subclip(
                current_duration - chunk_duration_sec, current_duration
            )
            current_duration -= chunk_duration_sec
            current_video = os.path.join(
                chunks_dir, f"{file_name}_{str(current_duration).replace('.','_')}.mp4"
            )
            clip.to_videofile(
                current_video,
                codec="libx264",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                audio_codec="aac",
            )

            chunks_path.append(current_video)
            clip.close()
        else:
            clip = VideoFileClip(processing_file_path).subclip(0, current_duration)
            current_video = os.path.join(
                chunks_dir, f"{file_name}_{str(0).replace('.','_')}.mp4"
            )
            clip.to_videofile(
                current_video,
                codec="libx264",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                audio_codec="aac",
            )

            chunks_path.append(current_video)
            clip.close()  # Release resources
    except Exception as e:
        print(e)
        pass

    processed_dir = processing_dir.replace("processing", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    try:
        shutil.move(processing_file_path, processed_dir)
    except Exception as e:
        print(str(e))
        pass
    return chunks_path[::-1]


def create_database_and_fetch_latest_id():
    # Specify the database file path in the parent directory
    database_file_path = os.path.join(PARENT_dIR, "smarteye.db")

    # Connect to the SQLite database or create a new one if not exists
    try:
        connection = sqlite3.connect(database_file_path)
        cursor = connection.cursor()

        # Create the table if not exists
        create_table_query = """
            CREATE TABLE IF NOT EXISTS smarteye (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                AlertName TEXT,
                Summary TEXT,
                Objects TEXT,
                VideoChunkPath TEXT,
                SourceVideoPath TEXT,
                Timestamp TEXT
            )
        """
        cursor.execute(create_table_query)

        # Fetch the latest ID
        fetch_latest_id_query = "SELECT id FROM smarteye ORDER BY Id DESC LIMIT 1"
        cursor.execute(fetch_latest_id_query)
        result = cursor.fetchone()

        # Return the latest ID (or 0 if not available)
        if result:
            latest_id = result[0]
        else:
            latest_id = 0

        # Commit the changes and close the connection
        connection.commit()
        connection.close()

        return latest_id

    except OperationalError as e:
        print(f"Error: {e}")
        return 0  # Return 0 if there's an error


def insert_data_into_table(json_data):
    database_file_path = os.path.join(PARENT_dIR, "smarteye.db")

    try:
        connection = sqlite3.connect(database_file_path)
        cursor = connection.cursor()

        # Extract data from the JSON object
        alert_name = json_data.get("AlertName", "")
        summary = json_data.get("Summary", "")
        objects = json_data.get("Objects", "")
        video_chunk_path = json_data.get("VideoChunkPath", "")
        source_video_path = json_data.get("SourceVideoPath", "")
        timestamp = json_data.get("Timestamp", "")

        # Insert data into the table
        insert_query = """
            INSERT INTO smarteye (
                AlertName, Summary, Objects, VideoChunkPath, SourceVideoPath, Timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
        """

        cursor.execute(
            insert_query,
            (
                alert_name,
                summary,
                objects,
                video_chunk_path,
                source_video_path,
                timestamp,
            ),
        )

        # Commit the changes and close the connection
        connection.commit()
        connection.close()

        print("Data inserted successfully.")

    except Exception as e:
        print(f"Error: {e}")
