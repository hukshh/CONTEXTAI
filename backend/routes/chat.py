from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.rag_service import rag_service

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    response = await rag_service.answer_question(request.question)
    return response
