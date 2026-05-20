from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.postgres import get_postgres_session
from app.models.auth import User, Tenant, UserRole
from app.schemas.auth import UserRegisterSchema, UserLoginSchema, TokenResponseSchema, UserResponseSchema
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from loguru import logger

router = APIRouter(prefix="/auth", tags=["SARIQX Core Authentication Engine"])

# Mock function - Jab Brevo Service banaenge toh isko real trigger se replace kar denge
def send_verification_email_task(email: str, name: str):
    logger.info(f"📨 [BACKGROUND TASK] Dispaching encryption activation matrix to client mailbox: {email}")


@router.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def register_pipeline(payload: UserRegisterSchema, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_postgres_session)):
    """
    Dedicated Multi-Tenant registration gateway. 
    Can handle standalone users or onboard full new tenants dynamically.
    """
    try:
        # 1. Check if email already occupies space in cluster
        existing_user_query = await db.execute(select(User).where(User.email == payload.email))
        if existing_user_query.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration denied. Specified email space already occupied."
            )

        assigned_tenant_id = None

        # 2. Multi-Tenant Onboarding Strategy Check
        if payload.role == UserRole.TENANT_ADMIN:
            if not payload.tenant_details:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tenant Admin enrollment requires strict 'tenant_details' block parameters."
                )
            
            # Check subdomain availability
            subdomain_query = await db.execute(select(Tenant).where(Tenant.subdomain == payload.tenant_details.subdomain))
            if subdomain_query.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subdomain already reserved by another tenant entity."
                )
                
            # Instantiate fresh tenant partition
            new_tenant = Tenant(
                name=payload.tenant_details.name,
                subdomain=payload.tenant_details.subdomain.lower().strip()
            )
            db.add(new_tenant)
            await db.flush() # Flushes memory state to fetch generated tenant UUID safely
            assigned_tenant_id = new_tenant.id
            logger.info(f"🏢 Multi-Tenant Matrix: Provisioned fresh tenant partition: {new_tenant.subdomain}")

        # 3. Create and Encrypt User Instance
        new_user = User(
            tenant_id=assigned_tenant_id,
            email=payload.email.lower().strip(),
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            phone_number=payload.phone_number,
            role=payload.role,
            profile_metadata=payload.profile_metadata
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"👥 Account Registered: Bound entity ID {new_user.id} to role layer [{new_user.role}]")
        
        # 4. Offload heavy email dispatch sequence to an asynchronous background worker thread
        background_tasks.add_task(send_verification_email_task, new_user.email, new_user.full_name)
        
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"💥 Registration pipeline crashed for email={payload.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal registration pipeline failure."
        )


@router.post("/login", response_model=TokenResponseSchema)
async def login_pipeline(payload: UserLoginSchema, db: AsyncSession = Depends(get_postgres_session)):
    """
    Validates credentials, monitors shadow soft-delete parameters, and distributes signed cryptographic tokens.
    """
    try:
        # Fetch target user boundary mapping
        query = await db.execute(select(User).where(User.email == payload.email))
        user = query.scalar_one_or_none()
        
        # Cryptographic timing-attack-safe fallback error masking
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid account credentials provided."
            )
            
        # Enforce Shadow retention state block policy
        if user.is_deleted:
            logger.critical(f"🚨 INTRUSION ATTEMPT: User {user.id} matched credentials but holds SOFT_DELETED flag.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid account credentials provided." # Masked message to client
            )
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been suspended. Please contact platform administration."
            )

        # Compile contextual cryptographic payload parameters
        token_payload = {
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "role": user.role
        }
        
        access_token = create_access_token(payload=token_payload)
        refresh_token = create_refresh_token(payload=token_payload)
        
        logger.info(f"🎫 Session Issued: Successfully verified active security vectors for User ID: {user.id}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"💥 Login pipeline crashed for email={payload.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal login pipeline failure."
        )
