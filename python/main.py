from fastapi import FastAPI, UploadFile, File
import shutil
import os
import uuid

from app import process_video
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
    file_id = str(uuid.uuid4())

    input_path = f"uploads/{file_id}.mp4"
    output_path = f"outputs/{file_id}.mp4"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("STEP 3: request received")

    process_video(input_path, model, output_path)

    print("STEP 4: processing done")
    return {"output": output_path}

@app.get("/")
def health():
    return {"status": "ok"}