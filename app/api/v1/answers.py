from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.db.postgres import get_postgres_session
from app.api.deps import get_current_user
from app.models.auth import User, UserRole
from app.models.doubt import Question, Answer, DoubtStatus, Attachment, AttachmentType
from app.schemas.answer import AnswerCreateSchema, AnswerResponseSchema

router = APIRouter(prefix="/doubts", tags=["SARIQX Core Resolution Engine"])

@router.post("/{question_id}/answer", response_model=AnswerResponseSchema, status_code=status.HTTP_201_CREATED)
async def post_resolution(
    question_id: str,
    payload: AnswerCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_postgres_session)
):
    """
    Submits a tutor resolution with compressed WebP attachments.
    Links images directly to the Answer node and flips Question state to RESOLVED.
    """
    
    # 1. SECURITY: Only authorized roles can post answers
    if current_user.role == UserRole.END_USER:
        raise HTTPException(status_code=403, detail="Students are not authorized to post official resolutions.")

    # 2. Fetch the target Question
    query = select(Question).where(Question.id == question_id)
    question = await db.scalar(query)
    
    if not question:
        raise HTTPException(status_code=404, detail="Target doubt node not found.")

    # 3. B2B TENANT ISOLATION: Cross-tenant restriction check
    if current_user.role in [UserRole.TENANT_ADMIN, UserRole.TENANT_MODERATOR]:
        if question.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Cross-tenant interactions are strictly prohibited.")

    # 4. Instantiate and push the Core Answer Node
    new_answer = Answer(
        question_id=question.id,
        solver_id=current_user.id,
        text_content=payload.text_content,
        is_ai_generated=False
    )
    db.add(new_answer)
    
    # ⚡ LAZY FLUSH: Database temporary push taaki 'new_answer.id' generate ho jaye
    await db.flush() 

    # 5. Map incoming attachment relative paths to this Answer ID
    if payload.attachments:
        for file_path in payload.attachments:
            new_attachment = Attachment(
                answer_id=new_answer.id, # ⚡ Linked with Answer directly!
                file_url=file_path,
                attachment_type=AttachmentType.ANSWER_IMAGE
            )
            db.add(new_attachment)
            
    # 6. STATE MUTATION: Automatically transition the question status
    question.status = DoubtStatus.RESOLVED
    
    # 7. ACID Transaction Commit (Save everything safely)
    await db.commit()
    await db.refresh(new_answer)
    
    # Explicitly load relation data for the output schema payload
    await db.refresh(new_answer, ['attachments'])
    
    logger.info(f"💡 Doubt Resolved: Question [{question.id}] closed by Tutor [{current_user.username}] with {len(payload.attachments)} attachments.")
    
    return new_answer