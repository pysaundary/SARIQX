from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.postgres import get_postgres_session
from app.api.deps import get_current_user
from app.models.auth import User
from app.models.doubt import Question
from app.schemas.doubt import QuestionCreateSchema, QuestionResponseSchema

router = APIRouter(prefix="/doubts", tags=["SARIQX Core Doubt Engine"])

@router.post("/ask", response_model=QuestionResponseSchema, status_code=status.HTTP_201_CREATED)
async def submit_question(
    payload: QuestionCreateSchema, 
    current_user: User = Depends(get_current_user), # ⚡ BINA TOKEN ENTRY BLOCK!
    db: AsyncSession = Depends(get_postgres_session)
):
    """
    Ingests a new student doubt into the resolution matrix.
    Automatically binds the question to the authenticated student and their tenant.
    """
    
    # Initialize Core Question Node
    new_question = Question(
        tenant_id=current_user.tenant_id, # Inherit tenant context from the user automatically
        student_id=current_user.id,
        subject=payload.subject,
        text_content=payload.text_content
    )
    
    db.add(new_question)
    await db.commit()
    await db.refresh(new_question)
    
    logger.info(f"❓ New Doubt Ingested: Subject [{new_question.subject}] by Student [{current_user.email}]")
    
    return new_question