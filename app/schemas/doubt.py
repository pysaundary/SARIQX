import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.doubt import DoubtStatus
from app.schemas.attachment import AttachmentResponseSchema # ⚡ NAYA IMPORT

class QuestionCreateSchema(BaseModel):
    subject: str = Field(..., min_length=2, max_length=100)
    text_content: str = Field(..., min_length=5)
    # ⚡ Frontend se array aayega jisme uploaded media ke relative_paths honge
    attachments: Optional[List[str]] = Field(default=[], description="List of relative media paths")

class QuestionResponseSchema(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID]
    student_id: uuid.UUID
    subject: str
    text_content: str
    status: DoubtStatus
    created_at: datetime
    
    # ⚡ Taaki GET API call pe frontend ko questions ke sath uski photos ka full URL bhi mile!
    attachments: List[AttachmentResponseSchema] = [] 
    
    class Config:
        from_attributes = True