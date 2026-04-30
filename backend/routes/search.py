from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.rag_service import rag_service
from services.retrieval_service import retrieval_service

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    selected_docs: list[str] = None

@router.post("/search")
async def search_endpoint(request: SearchRequest):
    if not request.query or not request.query.strip():
        return JSONResponse(status_code=400, content={"error": "Search query cannot be empty"})
        
    try:
        results = []
        seen_chunks = set()
        query_lower = request.query.lower()
        
        # 1. Full-Text Search Pass (Exact Matches)
        all_chunks = list(retrieval_service.metadata.values())
        for c in all_chunks:
            if request.selected_docs and c["document_name"] not in request.selected_docs:
                continue
                
            text = " ".join(c['text'].split())
            if text in seen_chunks:
                continue
                
            idx = text.lower().find(query_lower)
            if idx != -1:
                start = max(0, idx - 60)
                end = min(len(text), idx + len(query_lower) + 60)
                snippet = "..." + text[start:end].strip() + "..."
                
                doc_name = c['document_name']
                if len(doc_name) > 33 and doc_name[32] == '_':
                    doc_name = doc_name[33:]
                    
                results.append({
                    "document": doc_name,
                    "page": c['page_number'],
                    "snippet": snippet
                })
                seen_chunks.add(text)
                
            if len(results) >= 5:
                break
                
        # 2. Fallback to Semantic Search if NO exact matches found
        if len(results) == 0:
            query_embedding = rag_service.embedding_service.get_embedding(request.query)
            relevant_chunks = retrieval_service.search(query_embedding, k=10, selected_docs=request.selected_docs)
            
            for c in relevant_chunks:
                if len(results) >= 5:
                    break
                    
                text = " ".join(c['text'].split())
                if text in seen_chunks:
                    continue
                    
                snippet = text[:150].strip() + "..."
                
                doc_name = c['document_name']
                if len(doc_name) > 33 and doc_name[32] == '_':
                    doc_name = doc_name[33:]
                    
                results.append({
                    "document": doc_name,
                    "page": c['page_number'],
                    "snippet": snippet
                })
                seen_chunks.add(text)
                
        return {"results": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Internal server error during search"})
