"""
Routes for sending/receiving chat messages.
Calls app/services/conversation_engine.py to actually process a message.
"""
from fastapi import APIRouter
from app.schemas import MessageRequest
from app.services.conversation_engine import get_ai_response
from app.services.personality import get_companion , build_system_prompt
from app.services.memory import store_message, get_conversation_history
router = APIRouter()

@router.post("/message")
def send_message(request: MessageRequest):
    companion = get_companion(request.companion_id)
    system_prompt = build_system_prompt(companion)

    store_message(request.companion_id, "user",request.message)

    history = get_conversation_history(request.companion_id)
    reply = get_ai_response(history, system_prompt)


    store_message(request.companion_id, "model", reply)
    return {"reply": reply}