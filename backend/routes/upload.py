from fastapi import APIRouter, UploadFile, File
import os
import shutil
from backend.services.rag_service import rag_service

router = APIRouter()

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Trigger RAG processing
    num_chunks = await rag_service.process_document(file_path, file.filename)
    
    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "chunks_processed": num_chunks
    }
