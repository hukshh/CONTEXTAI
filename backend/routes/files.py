from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.services.rag_service import rag_service
import os

router = APIRouter()

class DeleteRequest(BaseModel):
    filename: str

@router.get("/files")
async def list_files():
    try:
        base_path = os.getenv("BASE_PATH", "./data")
        uploads_dir = os.path.join(base_path, "uploads")
        if not os.path.exists(uploads_dir):
            return {"files": []}
        
        all_files = [f for f in os.listdir(uploads_dir) if not f.startswith(".")]
        indexed_files = rag_service.retrieval_service.doc_to_ids.keys()
        files_with_status = []
        for f in all_files:
            files_with_status.append({
                "name": f,
                "isIndexed": f in indexed_files
            })
        return {"files": files_with_status}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Failed to list files"})


@router.delete("/delete-file")
async def delete_file(request: DeleteRequest):
    try:
        success = rag_service.delete_file(request.filename)
        if not success:
            return JSONResponse(status_code=404, content={"error": "File not found"})
        return {"message": f"Successfully deleted {request.filename}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Failed to delete file"})

@router.delete("/clear-all")
async def clear_all():
    try:
        rag_service.clear_all()
        return {"message": "All files and embeddings cleared"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Failed to clear all files"})
