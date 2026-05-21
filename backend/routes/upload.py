import os
import shutil
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from services.status_manager import status_manager
from services.rag_service import rag_service

logger = logging.getLogger(__name__)
router = APIRouter()

BASE_PATH = os.getenv("BASE_PATH", "./data")
UPLOAD_DIR = os.path.join(BASE_PATH, "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Set initial status to uploaded
    status_manager.update_status(unique_filename, "uploaded", progress=0.0)
    
    try:
        # Stream file to disk in chunks to avoid in-memory buffering for large files
        with open(file_path, "wb") as buffer:
            # Copy file contents incrementally
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Upload: Failed to save file {file.filename}: {e}")
        status_manager.update_status(unique_filename, "failed", error="File writing failed")
        raise HTTPException(status_code=500, detail="File upload saving failed.")
    
    # Check Celery flag
    use_celery = os.getenv("USE_CELERY", "false").lower().strip() == "true"
    
    if use_celery:
        try:
            from tasks import process_document_task
            process_document_task.delay(file_path, unique_filename)
            logger.info(f"Upload: Dispatched {unique_filename} processing to Celery.")
        except Exception as e:
            logger.error(f"Upload: Celery task dispatch failed: {e}. Falling back to BackgroundTasks.")
            background_tasks.add_task(rag_service.process_document, file_path, unique_filename)
    else:
        background_tasks.add_task(rag_service.process_document, file_path, unique_filename)
        logger.info(f"Upload: Dispatched {unique_filename} processing to FastAPI BackgroundTasks.")
        
    return {
        "message": "File uploaded and processing started in background",
        "filename": unique_filename,
        "status": "uploaded"
    }
