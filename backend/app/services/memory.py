from app.core.config import supabase
from sentence_transformers import SentenceTransformer
import math
from datetime import datetime, timezone
import json
from app.services.conversation_engine import client as groq_client

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

def store_memory(companion_id: str, content: str, memory_type: str = "episodic", strength: float = 1.0):
    embedding = embedding_model.encode(content).tolist()
    supabase.table("memories").insert({
        "companion_id": companion_id,
        "content": content,
        "embedding": embedding,
        "strength": strength,
        "memory_type": memory_type
    }).execute()

def extract_glossary_entry(prev_ai_message: str, user_message: str) -> dict | None:
    prompt = f"""Look at this exchange and decide if the user is explaining the meaning of an unfamiliar Hindi, Gujarati, or personal slang word/phrase.

Companion said: {prev_ai_message}
User replied: {user_message}

If the user explained a term's meaning, respond with ONLY this JSON, nothing else:
{{"term": "the word or phrase", "meaning": "what it means, in the user's own words"}}

If not, respond with ONLY this JSON:
{{"term": null, "meaning": null}}"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    try:
        data = json.loads(response.choices[0].message.content)
        if data.get("term") and data.get("meaning"):
            return data
    except (json.JSONDecodeError, AttributeError, KeyError):
        pass
    return None

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
        if m.get("memory_type") == "glossary":
            m["effective_strength"] = m["strength"]
        else:
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