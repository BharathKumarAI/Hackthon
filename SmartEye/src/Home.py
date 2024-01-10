import os
import sqlite3
import streamlit as st
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(layout="wide")
st.title("Smart Eye - Redefining Surveillance")

os.environ["GOOGLE_API_KEY"] = os.environ["API_KEY"]
genai.configure(api_key=os.environ["API_KEY"])
model = genai.GenerativeModel("gemini-pro")

current_dir = os.path.dirname(os.path.abspath(__file__))
PARENT_dIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)

db_path = os.path.join(PARENT_dIR, "current_alerts.db")
hist_db_path = os.path.join(PARENT_dIR, "smarteye.db")


# Function to get all alert history from the alert history database as a DataFrame
def get_alert_history():
    conn = sqlite3.connect(hist_db_path)
    query = "SELECT * FROM smarteye where AlertName != '' ORDER BY Timestamp DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# Function to get all alert history from the alert history database as a DataFrame
def get_event_history():
    conn = sqlite3.connect(hist_db_path)
    query = "SELECT * FROM smarteye ORDER BY Timestamp DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


start_str = "provide the summary of events below as pointer(s): \n"
alert_df = get_alert_history()
events_data = get_event_history()
events_info = events_data["Summary"].to_list()
result_string = "\n".join("- " + item for item in events_info)

final_str = start_str + result_string

response = model.generate_content(final_str)

# Section 1: Summary of Events
st.subheader("Summary of Events")
st.write(response.text)
# Display some statistics or summary information
# You can customize this based on your specific use case.
st.subheader("Event Statistics")
st.write(f"Total Events captured: {len(events_data)}")
st.write(f"Total Alerts Generated: {len(alert_df)}")
st.write(f"Latest Event Date: {events_data['Timestamp'].max()}")

# Section 2: Alerts table
st.subheader("Alerts Info")


# Display the alerts table using Streamlit's table component
st.table(alert_df[["AlertName", "Summary", "Objects"]])

# Section 3: Event table
st.subheader("Events Info")

# Display the event table using Streamlit's table component
st.table(events_data[["AlertName", "Summary", "Objects"]])

# Run the app using: streamlit run filename.py
