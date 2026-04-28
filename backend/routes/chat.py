from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return {
        "answer": "This is a placeholder response"
    }
