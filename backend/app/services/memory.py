"""
Memory Architecture (see docs/ARCHITECTURE.md, Section 2).
Responsible for:
- Short-term memory (current session)
- Long-term episodic memory (strength/decay/reinforcement)
- Glossary memory (personal slang, romanized regional language terms)
- Embedding + vector search retrieval
"""
from app.core.config import supabase

def store_message(companion_id: str, role: str, content: str):
    supabase.table("messages").insert({
        "companion_id": companion_id,
        "role": role,
        "content": content
    }).execute()

def get_conversation_history(companion_id: str, limit: int = 20) -> list:
    result = (
        supabase.table("messages")
        .select("*")
        .eq("companion_id", companion_id)
        .order("created_at")
        .limit(limit)
        .execute()
    )
    return result.data