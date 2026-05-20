import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Enum, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.auth import Base  

class DoubtStatus(str, enum.Enum):
    PENDING = "PENDING"               # Abhi abhi pucha gaya hai
    IN_PROGRESS = "IN_PROGRESS"       # AI ya koi Tutor ispe kaam kar raha hai
    RESOLVED = "RESOLVED"             # Answer mil gaya aur bacha khush hai
    REJECTED = "REJECTED"             # Spam, irrelevant ya galat image


class AttachmentType(str, enum.Enum):
    QUESTION_IMAGE = "QUESTION_IMAGE"
    ANSWER_IMAGE = "ANSWER_IMAGE"


# ==============================================================================
# ❓ THE QUESTION (DOUBT) NODE
# ==============================================================================
class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    # 🔗 Relational Linkages
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # 📝 Content Block
    subject: Mapped[str] = mapped_column(String(100), index=True, nullable=False) # e.g., Physics, Chemistry, Math
    text_content: Mapped[str] = mapped_column(Text, nullable=False) # OCR text or typed question
    
    # ⚙️ Operational Flags
    status: Mapped[DoubtStatus] = mapped_column(Enum(DoubtStatus), default=DoubtStatus.PENDING, index=True)
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(nullable=True) # AI ko kitna bharosa hai apne answer pe
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships (Cascading ensures clean DB on deletes)
    answers: Mapped[List["Answer"]] = relationship(back_populates="question", cascade="all, delete-orphan")
    attachments: Mapped[List["Attachment"]] = relationship(back_populates="question", cascade="all, delete-orphan")


# ==============================================================================
# 💡 THE ANSWER (RESOLUTION) NODE
# ==============================================================================
class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Solver ID nullable hai kyunki answer AI bhi toh de sakta hai bina kisi human intervention ke!
    solver_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    text_content: Mapped[Text] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    question: Mapped["Question"] = relationship(back_populates="answers")
    attachments: Mapped[List["Attachment"]] = relationship(back_populates="answer", cascade="all, delete-orphan")


# ==============================================================================
# 📎 THE MEDIA ATTACHMENT NODE (For Cloudinary / AWS S3 URLs)
# ==============================================================================
class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    # Hybrid linkage: Ya toh Question se juda hoga ya Answer se
    question_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=True)
    answer_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("answers.id", ondelete="CASCADE"), nullable=True)
    
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    attachment_type: Mapped[AttachmentType] = mapped_column(Enum(AttachmentType), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    question: Mapped[Optional["Question"]] = relationship(back_populates="attachments")
    answer: Mapped[Optional["Answer"]] = relationship(back_populates="attachments")