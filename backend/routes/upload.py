from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
import os
import shutil
import uuid
from backend.services.rag_service import rag_service

router = APIRouter()

BASE_PATH = os.getenv("BASE_PATH", "./data")
UPLOAD_DIR = os.path.join(BASE_PATH, "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    try:
        # Save file immediately
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return {"error": "File upload failed"}
    
    # Trigger RAG processing in the background
    background_tasks.add_task(rag_service.process_document, file_path, unique_filename)
    
    return {
        "message": "File uploaded and processing started in background",
        "filename": unique_filename
    }
