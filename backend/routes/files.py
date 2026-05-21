from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.rag_service import rag_service
from services.storage_service import storage_service
from services.status_manager import status_manager
import os

router = APIRouter()

class DeleteRequest(BaseModel):
    filename: str

@router.get("/files")
async def list_files():
    try:
        # List files from storage provider (Local, S3, or Supabase)
        all_files = storage_service.list_files()
        
        # Ensure we reload index to get latest indexed documents
        rag_service.retrieval_service.reload()
        indexed_files = rag_service.retrieval_service.doc_to_ids.keys()
        
        files_with_status = []
        for f in all_files:
            # Skip hidden files
            if f.startswith("."):
                continue
                
            status_data = status_manager.get_status(f)
            
            # Map status helper
            is_indexed = (status_data.get("status") == "ready") or (f in indexed_files)
            
            # If the file is indexed but status manager doesn't know it, set it to ready
            status_str = status_data.get("status", "unknown")
            progress_val = status_data.get("progress", 0.0)
            if f in indexed_files and status_str != "ready":
                status_str = "ready"
                progress_val = 100.0
                
            files_with_status.append({
                "name": f,
                "isIndexed": is_indexed,
                "status": status_str,
                "progress": progress_val,
                "error": status_data.get("error")
            })
            
        return {"files": files_with_status}
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Files: Failed to list: {e}")
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
