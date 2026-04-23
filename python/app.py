import cv2
import numpy as np
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
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    temp_raw = "temp_raw.avi"

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(temp_raw, fourcc, fps, (width, height))

    frame_count = 0
    processed_frames = 0

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

        cv2.putText(
            frame,
            label,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        out.write(frame)

        processed_frames += 1
        frame_count += 1

        # ✅ REAL PROGRESS (0 → 90%)
        progress = int((frame_count / total_frames) * 90)
        print(f"PROGRESS:{progress}", flush=True)

    cap.release()
    out.release()

    # ❌ Validate raw video
    if not os.path.exists(temp_raw) or os.path.getsize(temp_raw) == 0:
        raise Exception("Raw video was not created")

    # ✅ Final conversion (90 → 100%)
    print("PROGRESS:95", flush=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", temp_raw,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-acodec", "aac",
        output_path
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        raise Exception("FFmpeg conversion failed:\n" + result.stderr.decode())

    os.remove(temp_raw)

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise Exception("Final video not created")

    print("PROGRESS:100", flush=True)

    return output_path


def get_predictor_model():
    from model import Model
    return Model()