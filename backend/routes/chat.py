from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.rag_service import rag_service

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    selected_docs: list[str] = None

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    response = await rag_service.answer_question(request.question, selected_docs=request.selected_docs)
    return response
