from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.rag_service import rag_service

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    selected_docs: list[str] = None

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not request.question or not request.question.strip():
        return JSONResponse(status_code=400, content={"error": "Query cannot be empty"})
        
    try:
        response = await rag_service.answer_question(request.question, selected_docs=request.selected_docs)
        if "error" in response:
            return JSONResponse(status_code=500, content=response)
        return response
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Internal server error during chat processing"})
