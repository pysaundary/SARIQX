import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.attachment import AttachmentResponseSchema # ⚡ Dynamic URL Schema

class AnswerCreateSchema(BaseModel):
    text_content: str = Field(..., min_length=2, examples=["Here is the step by step solution for the integration."])
    # ⚡ Frontend se optimized image ke relative_paths ka array aayega
    attachments: Optional[List[str]] = Field(default=[], description="List of relative media paths for the answer")

class AnswerResponseSchema(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    solver_id: uuid.UUID
    text_content: str
    is_ai_generated: bool
    created_at: datetime
    
    # ⚡ Taaki Svelte frontend ko answer ke sath uski saari images ka dynamic Full URL mile
    attachments: List[AttachmentResponseSchema] = []
    
    class Config:
        from_attributes = True