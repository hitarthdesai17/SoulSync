"""Pydantic schemas defining the shape of API request/response data. Filled in during Phase 7."""
from pydantic import BaseModel

class MessageRequest(BaseModel):
    message: str
    companion_id: str