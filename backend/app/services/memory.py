from app.core.config import supabase
from sentence_transformers import SentenceTransformer
import math
from datetime import datetime, timezone

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

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
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(result.data))

def store_memory(companion_id: str, content: str):
    embedding = embedding_model.encode(content).tolist()
    supabase.table("memories").insert({
        "companion_id": companion_id,
        "content": content,
        "embedding": embedding,
        "strength": 1.0
    }).execute()

def get_relevant_memories(companion_id: str, query_text: str, threshold: float = 0.3, count: int = 5) -> list:
    query_embedding = embedding_model.encode(query_text).tolist()

    result = supabase.rpc("match_memories", {
        "query_embedding": query_embedding,
        "match_companion_id": companion_id,
        "match_threshold": threshold,
        "match_count": count
    }).execute()

    memories = result.data
    for m in memories:
        m["effective_strength"] = calculate_decayed_strength(m["strength"], m.get("last_reinforced_at") or m.get("created_at"))

    return memories

def reinforce_memory(memory_id: str):
    current = supabase.table("memories").select("strength").eq("id", memory_id).single().execute()
    new_strength = min(1.0, current.data["strength"] + 0.3)

    supabase.table("memories").update({
        "strength": new_strength,
        "last_reinforced_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", memory_id).execute()

def calculate_decayed_strength(strength: float, last_reinforced_at: str) -> float:
    last_reinforced = datetime.fromisoformat(last_reinforced_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    days_elapsed = (now - last_reinforced).total_seconds() / 86400
    decay_rate = 0.05
    return strength * math.exp(-decay_rate * days_elapsed)