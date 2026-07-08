"""
Personality Architecture (see docs/ARCHITECTURE.md, Section 1).
Responsible for:
- Core Identity fields (user-authored, stable)
- Adaptive Layer (evolves from conversation, constrained by Core)
- Seeding: turning freeform user description into structured fields
"""
from app.core.config import supabase
from app.schemas.companion import CompanionCreate

def create_companion(data: CompanionCreate) -> dict:
    result = supabase.table("companions").insert({
        "name": data.name,
        "relationship_type": data.relationship_type,
        "backstory": data.backstory,
        "speaking_style": data.speaking_style,
        "core_traits": data.core_traits
    }).execute()
    return result.data[0]

def get_companion(companion_id: str) -> dict:
    result = supabase.table("companions").select("*").eq("id", companion_id).single().execute()
    return result.data

def build_system_prompt(companion: dict) -> str:
    traits_text = ", ".join(f"{k}: {v}" for k, v in companion.get("core_traits", {}).items())
    backstory = companion.get("backstory") or "Not specified"
    speaking_style = companion.get("speaking_style") or "Natural and warm"

    return f"""You are {companion['name']}, a {companion['relationship_type']} to the user.
Backstory: {backstory}
Speaking style: {speaking_style}
Traits: {traits_text}

Stay consistent with this identity. Never claim to be a real person — you are an AI companion inspired by this description."""