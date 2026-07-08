"""
Routes for creating/editing companions (the Personality Profile from Phase 3).
Should stay 'thin' - just receive requests and call app/services/personality.py.
No real logic lives here.
"""
from fastapi import APIRouter
from app.schemas.companion import CompanionCreate
from app.services.personality import create_companion, get_companion

router = APIRouter()

@router.post("/companions")
def add_companion(data: CompanionCreate):
    return create_companion(data)

@router.get("/companions/{companion_id}")
def fetch_companion(companion_id: str):
    return get_companion(companion_id)