from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import shutil
import os
import uuid
import json
import cv2
import torch

from model import Model

app = FastAPI()

print("STEP 1: before model load")
model = Model(
    weights_dir="./weights",
    device="cpu"
)
print("STEP 2: model loaded")


@app.post("/process")
async def process(file: UploadFile = File(...)):

    def generate():
        file_id = str(uuid.uuid4())

        input_path = f"uploads/{file_id}.mp4"
        output_path = f"outputs/{file_id}.mp4"

        # ✅ Save file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print("STEP 3: request received")

        cap = cv2.VideoCapture(input_path)

        if not cap.isOpened():
            yield "PROGRESS:0\n"
            yield json.dumps({"error": "Cannot open video"})
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 20

        temp_raw = f"temp_{file_id}.avi"

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(temp_raw, fourcc, fps, (width, height))

        frame_count = 0
        last_progress = -1
        frame_skip = 5

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # skip frames
            if frame_count % frame_skip != 0:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            with torch.no_grad():
                result = model.predict(image=rgb)
                label = result["label"]

            cv2.putText(frame, label, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 255, 0), 2)

            out.write(frame)

            # ✅ REAL progress
            progress = int((frame_count / total_frames) * 100)

            # ✅ avoid duplicate spam
            if progress != last_progress:
                yield f"PROGRESS:{progress}\n"
                last_progress = progress

        cap.release()
        out.release()

        # ✅ Convert to MP4
        final_path = output_path
        os.system(
            f"ffmpeg -y -loglevel error -i {temp_raw} -vcodec libx264 -pix_fmt yuv420p {final_path}"
        )

        os.remove(temp_raw)

        print("STEP 4: processing done")

        # ✅ Ensure final 100
        yield "PROGRESS:100\n"

        # ✅ Final JSON
        yield json.dumps({"output": final_path})

    return StreamingResponse(generate(), media_type="text/plain")


@app.get("/")
def health():
    return {"status": "ok"}