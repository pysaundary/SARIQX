import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.doubt import DoubtStatus

class QuestionCreateSchema(BaseModel):
    subject: str = Field(..., min_length=2, max_length=100, examples=["Physics"])
    text_content: str = Field(..., min_length=5, examples=["What is the formula for escape velocity?"])
    # Hum API se student_id nahi mangenge, wo token se automatic nikalenge (Security protocol!)

class QuestionResponseSchema(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID]
    student_id: uuid.UUID
    subject: str
    text_content: str
    status: DoubtStatus
    created_at: datetime
    
    class Config:
        from_attributes = True