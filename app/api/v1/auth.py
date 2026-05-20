from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.postgres import get_postgres_session
from app.models.auth import User, Tenant, UserRole
from app.schemas.auth import UserRegisterSchema, UserLoginSchema, TokenResponseSchema, UserResponseSchema
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from loguru import logger
from app.services.email import BrevoEmailService
from fastapi.responses import HTMLResponse
from app.schemas.auth import RefreshTokenRequestSchema

router = APIRouter(prefix="/auth", tags=["SARIQX Core Authentication Engine"])

async def send_verification_email_task(email: str, name: str, token: str):
    """Fires transactional sequence inside background threading loops cleanly"""
    await BrevoEmailService.send_verification(email, name, token)


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
        from datetime import timedelta
    
        verify_payload = {
            "user_id": str(new_user.id),
            "type": "email_verification"
        }
        verification_token = create_access_token(payload=verify_payload, expires_delta=timedelta(hours=24))
        background_tasks.add_task(send_verification_email_task, new_user.email, new_user.full_name, verification_token)
        
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

@router.get("/verify", response_class=HTMLResponse)
async def verify_email_pipeline(token: str, db: AsyncSession = Depends(get_postgres_session)):
    """
    Stateless Email Verification execution block.
    Intercepts GET requests from email clients, validates JWT signatures, and activates users.
    """
    from app.core.security import decode_token
    
    try:
        # Cryptographic unwrapping of the token
        payload = decode_token(token)
        
        # Strict semantic boundary check
        if payload.get("type") != "email_verification":
            raise ValueError("Token semantic boundary mismatch.")
            
        user_id = payload.get("user_id")
        
        # Fetch target user from relational node
        query = await db.execute(select(User).where(User.id == user_id))
        user = query.scalar_one_or_none()
        
        if not user:
            return HTMLResponse(
                content="<h2 style='color: red; font-family: sans-serif; text-align: center; margin-top: 50px;'>❌ Security Error: Account mapping not found in system.</h2>", 
                status_code=400
            )
            
        if user.is_verified:
            return HTMLResponse(
                content="<h2 style='color: #4F46E5; font-family: sans-serif; text-align: center; margin-top: 50px;'>✅ Email is already verified! You can close this window and login.</h2>"
            )
            
        # 🔑 Core Execution: Flip the verification boolean state
        user.is_verified = True
        await db.commit()
        
        logger.info(f"✅ Identity Verified: Structural clearances upgraded for User ID: {user.id}")
        
        return HTMLResponse(
            content="""
            <div style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                <h1 style="color: #10B981;">✅ Activation Successful!</h1>
                <p style="color: #4B5563;">Your email address has been securely verified. SARIQX engine is ready.</p>
                <p style="font-size: 14px; color: #9CA3AF;">You may now safely close this window.</p>
            </div>
            """
        )
        
    except ValueError as err:
        logger.error(f"🛡️ Email Verification Intercept: Cryptographic signature failure: {err}")
        return HTMLResponse(
            content="<h2 style='color: red; font-family: sans-serif; text-align: center; margin-top: 50px;'>❌ The verification link is invalid, corrupted, or has expired.</h2>", 
            status_code=400
        )

@router.post("/refresh", response_model=TokenResponseSchema, status_code=status.HTTP_200_OK)
async def refresh_access_token(payload: RefreshTokenRequestSchema, db: AsyncSession = Depends(get_postgres_session)):
    """
    Consumes a valid refresh token, verifies user active status, 
    and mints a fresh pair of cryptographic tokens (Token Rotation).
    """
    from app.core.security import decode_token, create_refresh_token
    
    try:
        # Step A: Cryptographically unwrap the refresh token
        token_payload = decode_token(payload.refresh_token)
        
        # Step B: Strict boundary validation
        if token_payload.get("type") != "refresh":
            raise ValueError("Provided signature is not a valid refresh token.")

        user_id = token_payload.get("user_id")
        
        # Step C: Database Verification Check
        # Yeh check karna zaroori hai ki picchle 7 din (refresh expiry) mein 
        # kisi admin ne is user ko delete ya suspend toh nahi kar diya!
        query = await db.execute(select(User).where(User.id == user_id))
        user = query.scalar_one_or_none()
        
        if not user or user.is_deleted or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ACCOUNT_SUSPENDED"
            )

        # Step D: Compile fresh security payload
        new_token_payload = {
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "role": user.role
        }
        
        # Step E: Mint new tokens (Rotation Strategy)
        new_access_token = create_access_token(payload=new_token_payload)
        new_refresh_token = create_refresh_token(payload=new_token_payload)

        logger.info(f"🔄 Token Rotated: Fresh session issued for User ID: {user.id}")

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer"
        }
        
    except Exception as e:
        logger.error(f"🛡️ Token Refresh Intercept: Signature invalid or expired: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_REFRESH_TOKEN", # Frontend will catch this and FORCE LOGOUT
            headers={"WWW-Authenticate": "Bearer"},
        )