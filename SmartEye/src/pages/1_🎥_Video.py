import av
import os
from aiortc.contrib.media import MediaRecorder
import streamlit as st
import datetime

from streamlit_webrtc import (
    VideoProcessorBase,
    WebRtcMode,
    webrtc_streamer,
)

st.set_page_config(layout="wide")

# Get the directory of the current script or module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)
# Navigate to the parent directory and then to the "captured/video" directory
video_dir = os.path.join(
    os.path.abspath(os.path.join(parent_dir, os.pardir)), "captured", "video"
)
print(video_dir)


class SaveVideoProcessor(VideoProcessorBase):
    def __init__(self, filepath):
        self.filepath = filepath
        self.recorder = None

    def open(self):
        self.recorder = av.open(self.filepath, "w")

    def close(self):
        if self.recorder:
            self.recorder.close()

    def recv(self, frame):
        if self.recorder:
            self.recorder.mux(frame)


def app():
    st.sidebar.title("Video Upload and Save")

    uploaded_file = st.sidebar.file_uploader(
        "Choose a video file", type=["mp4", "avi", "mkv"]
    )

    def in_recorder_factory() -> MediaRecorder:
        return MediaRecorder(
            os.path.join(
                video_dir,
                f"camera_feed_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4",
            ),
            format="mp4",
        )  # HLS does not work. See https://github.com/aiortc/aiortc/issues/331

    webrtc_streamer(
        key="loopback",
        in_recorder_factory=in_recorder_factory,
        # out_recorder_factory=out_recorder_factory,
    )

    if uploaded_file is not None:
        st.sidebar.write("File uploaded successfully!")

        save_path = os.path.join(
            video_dir,
            f"uploaded_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4",
        )
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.sidebar.write(f"Saved to: {save_path}")

    # else:
    #     st.warning("Please upload a video file in the sidebar.")


if __name__ == "__main__":
    app()
