"""
Routes for sending/receiving chat messages.
Calls app/services/conversation_engine.py to actually process a message.
"""
from fastapi import APIRouter
from app.schemas import MessageRequest
from app.services.conversation_engine import get_ai_response

router = APIRouter()
@router.post("/message")
def send_message(request: MessageRequest):
    reply = get_ai_response(request.message)
    return {"reply": reply}