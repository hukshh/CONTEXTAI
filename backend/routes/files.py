from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.rag_service import rag_service
import os

router = APIRouter()

class DeleteRequest(BaseModel):
    filename: str

@router.get("/files")
async def list_files():
    """Returns a list of all uploaded filenames with their indexing status."""
    if not os.path.exists("uploads"):
        return {"files": []}
    
    all_files = [f for f in os.listdir("uploads") if f.endswith(".pdf")]
    indexed_files = rag_service.retrieval_service.doc_to_ids.keys()
    
    files_with_status = []
    for f in all_files:
        files_with_status.append({
            "name": f,
            "isIndexed": f in indexed_files
        })
        
    return {"files": files_with_status}

@router.get("/stats")
async def get_stats():
    """Returns debug information about the vector index."""
    return {
        "total_chunks": rag_service.retrieval_service.index.ntotal,
        "indexed_documents": list(rag_service.retrieval_service.doc_to_ids.keys()),
        "metadata_count": len(rag_service.retrieval_service.metadata)
    }

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
