from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.models.doubt import Attachment, AttachmentType
from app.db.postgres import get_postgres_session
from app.api.deps import get_current_user
from app.models.auth import User
from app.models.doubt import Question
from app.schemas.doubt import QuestionCreateSchema, QuestionResponseSchema
from typing import Optional
from sqlalchemy import select, func
from app.models.auth import UserRole
from app.models.doubt import DoubtStatus
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload
from app.models.doubt import Answer
import uuid
router = APIRouter(prefix="/doubts", tags=["SARIQX Core Doubt Engine"])

@router.post("/ask", response_model=QuestionResponseSchema, status_code=status.HTTP_201_CREATED)
async def submit_question(
    payload: QuestionCreateSchema, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_session)
):
    # 1. Base Question create karo
    new_question = Question(
        tenant_id=current_user.tenant_id,
        student_id=current_user.id,
        subject=payload.subject,
        text_content=payload.text_content
    )
    
    db.add(new_question)
    await db.flush() # 
    
    # 2. Agar frontend ne attachments bheje hain, toh unko Question se link karo
    if payload.attachments:
        for file_path in payload.attachments:
            new_attachment = Attachment(
                question_id=new_question.id, 
                file_url=file_path,
                attachment_type=AttachmentType.QUESTION_IMAGE
            )
            db.add(new_attachment)
            
    # 3. Final Commit (Save everything together in one transaction)
    await db.commit()
    await db.refresh(new_question)
    
    # Refreshing relationships explicitly to load attachments into response
    await db.refresh(new_question, ['attachments'])
    
    logger.info(f"❓ Doubt Ingested: Subject [{new_question.subject}] with {len(payload.attachments)} attachments by [{current_user.username}]")
    
    return new_question

@router.get("/feed", status_code=status.HTTP_200_OK)
async def list_doubts(
    status: Optional[DoubtStatus] = None,
    subject: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_session)
):
    """
    Fetches paginated and filtered list of doubts based on strict Role-Based Access Control (RBAC).
    Guarantees B2B data isolation.
    """
    
    # 1. Base Query aur Count Query setup
    query = select(Question).options(selectinload(Question.attachments)) # ⚡ MAGIC LOAD
    count_query = select(func.count()).select_from(Question)
    
    # 🛡️ 2. DATA ISOLATION MATRIX (The Magic)
    if current_user.role == UserRole.END_USER:
        # Student isolation: Only their own questions
        query = query.where(Question.student_id == current_user.id)
        count_query = count_query.where(Question.student_id == current_user.id)
        
    elif current_user.role in [UserRole.TENANT_ADMIN, UserRole.TENANT_MODERATOR]:
        # Tenant isolation: Only questions belonging to their specific institute boundary
        query = query.where(Question.tenant_id == current_user.tenant_id)
        count_query = count_query.where(Question.tenant_id == current_user.tenant_id)
        
    # Super admins require no boundary restrictions, so no WHERE clause for them!

    # 3. Dynamic Search Filters
    if status:
        query = query.where(Question.status == status)
        count_query = count_query.where(Question.status == status)
        
    if subject:
        # Case-insensitive partial match search (e.g., "phys" will find "Physics")
        query = query.where(Question.subject.ilike(f"%{subject}%"))
        count_query = count_query.where(Question.subject.ilike(f"%{subject}%"))

    # 4. Pagination & Sorting Execution
    offset = (page - 1) * size
    query = query.order_by(Question.created_at.desc()).offset(offset).limit(size)
    
    total_elements = await db.scalar(count_query)
    results = await db.execute(query)
    questions = results.scalars().all()
    
    logger.info(f"📊 Doubt Feed Accessed: User [{current_user.email}] fetched {len(questions)} records.")
    
    return {
        "items": questions,
        "total": total_elements or 0,
        "page": page,
        "size": size,
        "total_pages": ((total_elements or 0) + size - 1) // size
    }


@router.get("/{question_id}", status_code=status.HTTP_200_OK)
async def get_single_doubt(
    question_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_session)
):
    """
    Fetches a specific doubt by ID. Contains security checks to prevent IDOR attacks.
    """
    query = select(Question).options(
    selectinload(Question.attachments),
    selectinload(Question.answers).selectinload(Answer.attachments)
).where(Question.id == question_id) 
    question = await db.scalar(query)
    
    if not question:
        raise HTTPException(status_code=404, detail="Doubt node not found in system.")
        
    # 🛡️ IDOR Protection: Agar student dusre student ke question ka ID daal de url me!
    if current_user.role == UserRole.END_USER and question.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to access this record.")
        
    if current_user.role in [UserRole.TENANT_ADMIN, UserRole.TENANT_MODERATOR] and question.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Record exists outside your tenant boundary.")
        
    return question 