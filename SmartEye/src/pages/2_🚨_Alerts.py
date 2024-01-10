import os
import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(layout="wide")
current_dir = os.path.dirname(os.path.abspath(__file__))
PARENT_dIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)
ROOT_DIR = os.path.abspath(os.path.join(PARENT_dIR, os.pardir))
db_path = os.path.join(ROOT_DIR, "current_alerts.db")
hist_db_path = os.path.join(ROOT_DIR, "smarteye.db")


# Function to create databases and tables
def create_current_database():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS current_alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 Name TEXT, Description TEXT, Type TEXT, Active BOOLEAN DEFAULT 1, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"""
    )
    conn.commit()
    conn.close()


# Function to create history database
def create_history_database():
    conn = sqlite3.connect(hist_db_path)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS alert_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 Name TEXT, Description TEXT, Type TEXT, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"""
    )
    conn.commit()
    conn.close()


# Function to add a new alert to the current alerts database
def add_current_alert(alert_name, alert_description, alert_type="Default"):
    if alert_name and alert_description:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO current_alerts (Name, Description, Type) VALUES (?, ?, ?)",
            (alert_name, alert_description, alert_type),
        )
        conn.commit()
        conn.close()
    else:
        st.sidebar.warning("Name/Description is not defined")


# Function to get all current alerts from the current alerts database as a DataFrame
def get_current_alerts():
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM current_alerts ORDER BY Timestamp DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# Function to get all alert history from the alert history database as a DataFrame
def get_alert_history():
    conn = sqlite3.connect(hist_db_path)
    query = "SELECT * FROM smarteye where AlertName != '' ORDER BY Timestamp DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# Function to deactivate alerts
def deactivate_selected_alerts(alert_ids):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for alert_id in alert_ids:
        c.execute("UPDATE current_alerts SET Active = 0 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()


# Function to reactivate alerts
def reactivate_selected_alerts(alert_ids):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for alert_id in alert_ids:
        c.execute("UPDATE current_alerts SET Active = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()


# Function to plot an interactive pie chart of active alerts using Plotly
def plot_pie_chart(df):
    if not df.empty and "AlertName" in df.columns:
        # active_df = df[df["Active"] == 1]

        fig = px.pie(
            df,
            names="AlertName",
            title="Active Alerts Distribution",
            labels={"AlertName": "Alert Name"},
            hole=0.3,
        )

        st.plotly_chart(fig)

    elif not df.empty:
        st.warning("No 'Name' column found in the DataFrame.")
    else:
        st.warning("No data available for previous alerts.")


# Main Streamlit app
def main():
    st.title("Alerts Dashboard")

    # Create databases if not exists
    create_current_database()
    create_history_database()

    # Display all current alerts from the current alerts database
    current_alerts_df = get_current_alerts()

    # Initialize variables for alert_name and alert_description
    alert_name = ""
    alert_description = ""

    with st.sidebar:
        with st.expander("New Alert"):
            # Add a new alert to the current alerts database
            with st.form("add_form", clear_on_submit=True):
                # Enclose input fields and button within a form
                alert_name = st.text_input("Alert Name", key="alert_name")
                alert_description = st.text_area(
                    "Alert Description", key="alert_description"
                )
                alert_type = st.selectbox("Alert Type", ["Default", "Custom"])
                if st.form_submit_button(
                    label="Add Alert",
                    on_click=add_current_alert,
                    args=(alert_name, alert_description, alert_type),
                ):
                    # Add the alert to the database
                    st.success("Alert added successfully!")
                    current_alerts_df = get_current_alerts()

        if not current_alerts_df.empty:
            with st.expander("Deactivate Alerts"):
                with st.form("deac_form", clear_on_submit=True):
                    # Employ st.multiselect outside the form to work around Streamlit's limitation
                    selected_alert_ids = st.multiselect(
                        "Select alerts to deactivate",
                        current_alerts_df[current_alerts_df["Active"] == 1]["id"],
                        key="deactive_alert",
                    )

                    if st.form_submit_button(label="Deactivate Alerts"):
                        # Deactivate alerts within the form submission context
                        deactivate_selected_alerts(selected_alert_ids)
                        st.success("Alerts deactivated successfully!")
                        current_alerts_df = get_current_alerts()

            with st.expander("Reactivate Alerts"):
                with st.form("reac_form", clear_on_submit=True):
                    deactivated_alerts = current_alerts_df[
                        current_alerts_df["Active"] == 0
                    ]

                    if not deactivated_alerts.empty:
                        # Display multiselect if there are deactivated alerts
                        selected_alert_ids = st.multiselect(
                            "Select alerts to reactivate",
                            current_alerts_df[current_alerts_df["Active"] == 0]["id"],
                            key="reactive_alert",
                        )

                        if st.form_submit_button(label="Reactivate Alerts"):
                            reactivate_selected_alerts(selected_alert_ids)
                            st.success("Alerts reactivated successfully!")
                            current_alerts_df = get_current_alerts()
                            # Clear form fields
                            alert_name = ""
                            alert_description = ""
                        else:
                            # Display message if no deactivated alerts are available
                            st.info("No deactivated alerts available.")

    if not current_alerts_df.empty:
        # Display all current alerts as a DataFrame
        st.header("Current Alerts")
        st.dataframe(current_alerts_df)

        # Display interactive pie chart of active alerts
        st.header("Active Alerts Distribution")
        plot_pie_chart(get_alert_history())
    else:
        st.warning("No current alerts.")

    # Display alert history
    st.header("Alert History")
    alert_history_df = get_alert_history()

    if not alert_history_df.empty:
        # Display all alert history as a DataFrame
        st.dataframe(alert_history_df)
    else:
        st.warning("No alert history.")


if __name__ == "__main__":
    main()
