"""
Routes for sending/receiving chat messages.
Calls app/services/conversation_engine.py to actually process a message.
"""
from fastapi import APIRouter
from app.schemas import MessageRequest
from app.services.conversation_engine import get_ai_response
from app.services.personality import get_companion, build_system_prompt
from app.services.memory import (
    store_message, get_conversation_history, store_memory,
    get_relevant_memories, reinforce_memory, extract_glossary_entry
)

router = APIRouter()

from app.services.memory import store_message, get_conversation_history, store_memory, get_relevant_memories, reinforce_memory

@router.post("/message")
def send_message(request: MessageRequest):
    companion = get_companion(request.companion_id)
    base_prompt = build_system_prompt(companion)

    relevant_memories = get_relevant_memories(request.companion_id, request.message)
    if relevant_memories:
        memory_text = "\n".join(f"- {m['content']} (confidence: {m['effective_strength']:.2f})" for m in relevant_memories)
        system_prompt = f"{base_prompt}\n\nRelevant things you remember:\n{memory_text}\n\nIf a memory's confidence is low, express appropriate uncertainty rather than stating it as fact."
        for m in relevant_memories:
            reinforce_memory(m["id"])
    else:
        system_prompt = base_prompt

    store_message(request.companion_id, "user", request.message)
    store_memory(request.companion_id, request.message)

    history = get_conversation_history(request.companion_id)

    if len(history) >= 2 and history[-2]["role"] == "model":
        glossary_entry = extract_glossary_entry(history[-2]["content"], request.message)
        if glossary_entry:
            store_memory(
                request.companion_id,
                f"{glossary_entry['term']} means {glossary_entry['meaning']}",
                memory_type="glossary"
            )
    reply = get_ai_response(history, system_prompt)

    store_message(request.companion_id, "model", reply)

    return {"reply": reply}