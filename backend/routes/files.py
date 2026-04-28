from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.rag_service import rag_service
import os

router = APIRouter()

class DeleteRequest(BaseModel):
    filename: str

@router.get("/files")
async def list_files():
    """Returns a list of all uploaded filenames."""
    if not os.path.exists("uploads"):
        return {"files": []}
    files = [f for f in os.listdir("uploads") if f.endswith(".pdf")]
    return {"files": files}

@router.delete("/delete-file")
async def delete_file(request: DeleteRequest):
    success = rag_service.delete_file(request.filename)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"message": f"Successfully deleted {request.filename}"}

@router.delete("/clear-all")
async def clear_all():
    rag_service.clear_all()
    return {"message": "All files and embeddings cleared"}
