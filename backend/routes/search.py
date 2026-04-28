from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.rag_service import rag_service
from backend.services.embedding_service import EmbeddingService
from backend.services.retrieval_service import retrieval_service

router = APIRouter()
embedding_service = EmbeddingService()

class SearchRequest(BaseModel):
    query: str
    selected_docs: list[str] = None

@router.post("/search")
async def search_endpoint(request: SearchRequest):
    # 1. Convert query to embedding
    query_embedding = embedding_service.get_embedding(request.query)
    
    # 2. Retrieve top-k chunks (k=5) with filtering
    relevant_chunks = retrieval_service.search(query_embedding, k=5, selected_docs=request.selected_docs)
    
    # 3. Format results with snippets
    results = []
    seen_pages = set()
    
    for c in relevant_chunks:
        page_key = f"{c['document_name']}_{c['page_number']}"
        if page_key not in seen_pages:
            # Clean snippet logic (reusing logic from rag_service for consistency)
            text = " ".join(c['text'].split())
            limit = 150
            if len(text) > limit:
                snippet = text[:limit].rsplit(' ', 1)[0] + "..."
            else:
                snippet = text
                
            results.append({
                "document": c['document_name'],
                "page": c['page_number'],
                "snippet": snippet
            })
            seen_pages.add(page_key)
        
        if len(results) >= 5:
            break
            
    return {"results": results}
