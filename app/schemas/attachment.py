import uuid
from datetime import datetime
from pydantic import BaseModel, Field, computed_field
from app.models.doubt import AttachmentType
from app.core.collector import collector

class AttachmentCreateSchema(BaseModel):
    file_url: str = Field(..., description="The relative path returned by storage provider.")
    attachment_type: AttachmentType

class AttachmentResponseSchema(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID | None
    answer_id: uuid.UUID | None
    attachment_type: AttachmentType
    created_at: datetime
    
    # ❌ Database mein sirf relative path rahega (e.g., /media/tenant/...)
    file_url: str = Field(..., exclude=True) # Ise direct JSON mein bhejone se rokenge

    # ⚡ THE MAGIC COMPUTED FIELD
    @computed_field
    def full_url(self) -> str:
        """
        Dynamically prepends the base URL from .env to the relative storage path.
        Keeps DB clean, keeps frontend happy!
        """
        base_url = collector.get("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")
        # Ensure path starts with a single slash
        relative_path = self.file_url if self.file_url.startswith("/") else f"/{self.file_url}"
        return f"{base_url}{relative_path}"

    class Config:
        from_attributes = True