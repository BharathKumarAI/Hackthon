import streamlit as st

st.set_page_config(layout="wide")
st.title("Smart Eye - Redefining Surveillance")

# Create tabs
tab_titles = [
    "Live Feed",
    "Daily Event Summary",
    "Alerts",
    "Chat Interface",
]
tabs = st.tabs(tab_titles)

# Add content to the Data Preprocessing tab
with tabs[0]:
    st.subheader("Live Feed")
    st.write("This is where you can include your sources for video feed.")
    with st.sidebar:
        st.subheader("sidebar")

# Add content to the Model Training tab
with tabs[1]:
    st.subheader("Daily Event Summary")
    st.write("Summary of key of event on daily basis")

# Add content to the Model Evaluation tab
with tabs[2]:
    st.subheader("Alerts")
    st.write(
        "This is where you can set the custom alertsa and see the past alerts that are generated."
    )

# Add content to the Results Visualization tab
with tabs[3]:
    st.subheader("Chat Interface")
    st.write("This is where you can use the chat interface.")
