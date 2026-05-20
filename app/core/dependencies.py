# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token
from app.db.postgres import get_postgres_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_postgres_session)
) -> dict:
    """
    Strict Dependency Guard for Protected Routes.
    Intercepts token signature, parses internal flags, and masquerades deleted accounts externally.
    """
    if not credentials:
        logger.warning("🛡️ Auth Guard: Missing Authorization bearer token in request header headers.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = credentials.credentials
    try:
        # 1. Cryptographically decode using our core security engine
        payload = decode_token(token)
        
        if payload.get("type") != "access":
            raise ValueError("Token semantic type context mismatch.")
            
        user_id = payload.get("user_id")
        
        # 2. Database Layer Verification: Check internal retention policy state
        # High speed single row index query execution
        result = await db.execute(
            text("SELECT is_active, is_deleted, deleted_at FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        user_state = result.fetchone()
        
        if not user_state:
            logger.warning(f"🚫 Security Trace: Token valid but user_id {user_id} does not exist in relational cluster.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session account context.")
            
        is_active, is_deleted, deleted_at = user_state
        
        # 3. INTERNAL LOGGING AND EXTERNAL MASQUERADING
        if is_deleted:
            # Internal Log: Hamein pata hai ki soft deleted state mein retention hold par hai
            logger.critical(
                f"🚨 INT_SECURITY_SHADOW_LOG: User {user_id} attempted access! "
                f"Status: SOFT_DELETED | Retention Timer Triggered At: {deleted_at}. Access Blocked."
            )
            # External Presentation: Client ko bolenge tera user context hi galat hai (Masquerading)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Authentication failed. Account has been deactivated or removed."
            )
            
        if not is_active:
            logger.warning(f"⚠️ Account Suspended: User {user_id} detected with is_active=False toggle. Denying access.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Your account is temporarily deactivated."
            )
            
        return payload 
        
    except ValueError as err:
        logger.error(f"🛡️ Auth Guard Trace: Verification failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature has expired or is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )