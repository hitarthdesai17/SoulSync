from pydantic import BaseModel
from typing import Optional

class CompanionCreate(BaseModel):
    name: str
    relationship_type: str
    backstory: Optional[str] = None
    speaking_style: Optional[str] = None
    core_traits: dict = {}