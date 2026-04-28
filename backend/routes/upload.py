from fastapi import APIRouter, UploadFile, File, BackgroundTasks
import os
import shutil
from backend.services.rag_service import rag_service

router = APIRouter()

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save file immediately
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Trigger RAG processing in the background
    background_tasks.add_task(rag_service.process_document, file_path, file.filename)
    
    return {
        "message": "File uploaded and processing started in background",
        "filename": file.filename
    }
