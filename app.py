import cv2
import numpy as np
import streamlit as st
from PIL import Image
import torch
import os

import subprocess

def process_video(video_path, model, output_path="output.mp4"):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception("Error opening video file")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 20

    temp_raw = "temp_raw.avi"

    # ✅ Use AVI for raw writing (more reliable in OpenCV)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(temp_raw, fourcc, fps, (width, height))

    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # skip frames (CPU optimization)
        if frame_count % 5 != 0:
            frame_count += 1
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        with torch.no_grad():
            result = model.predict(image=rgb)
            label = result["label"]

        cv2.putText(frame, label, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2)

        out.write(frame)
        frame_count += 1

    cap.release()
    out.release()

    # ❌ If OpenCV output failed
    if not os.path.exists(temp_raw) or os.path.getsize(temp_raw) == 0:
        raise Exception("Raw video was not created")

    # ✅ Convert to browser-compatible MP4 (THIS is the real fix)
    cmd = [
        "ffmpeg",
        "-y",
        "-i", temp_raw,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-acodec", "aac",
        output_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        raise Exception("FFmpeg conversion failed:\n" + result.stderr.decode())

    # cleanup
    os.remove(temp_raw)

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise Exception("Final video not created")

    return output_path

# ✅ modern cache (fixes deprecation issues)
@st.cache_resource
def get_predictor_model():
    from model import Model
    return Model()


# UI
st.title('Violence Detection')
st.text('Upload an image or video to detect violence-related content.')

uploaded_file = st.file_uploader("Upload Image or Video", type=["jpg", "png", "mp4"])

if uploaded_file is not None:

    file_type = uploaded_file.type

    # save uploaded file
    temp_path = "temp_file"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    model = get_predictor_model()

    if "video" in file_type:
        st.write("Processing video... (this may take time ⏳)")

        try:
            output_path = process_video(temp_path, model)

            st.success("Video processed!")

            # ✅ FIX: read file as bytes (important)
            with open(output_path, "rb") as f:
                st.video(f.read())

        except Exception as e:
            st.error(f"Error processing video: {e}")

    else:
        # image processing
        result = model.predict(image=temp_path)
        st.write(result)