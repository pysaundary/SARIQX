from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import jwt  # ⚡ Import JWT to catch specific library errors

from app.db.postgres import get_postgres_session
from app.models.auth import User
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_postgres_session)) -> User:
    """
    Decodes the JWT, verifies the 'access' scope, and fetches the real user.
    Provides clear error codes for frontend interceptors to trigger silent refreshes.
    """
    try:
        # Cryptographic unwrapping
        payload = decode_token(token)
        
        if payload.get("type") != "access":
            raise ValueError("Token is not an access token.")
            
        user_id = payload.get("user_id")
        if user_id is None:
            raise ValueError("User ID missing in payload.")
            
    except jwt.ExpiredSignatureError:
        # ⚡ FRONTEND SIGNAL 1: Token specifically expired. 
        # Svelte will catch this "TOKEN_EXPIRED" and fire the refresh token API silently.
        logger.warning("🛡️ Auth Intercept: Access token expired.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOKEN_EXPIRED", 
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # ⚡ FRONTEND SIGNAL 2: Token is tampered or completely invalid.
        # Svelte will catch this and instantly LOGOUT the user.
        logger.warning(f"🛡️ Auth Intercept: Invalid or tampered token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_TOKEN",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch fresh user state from Relational Pool
    query = await db.execute(select(User).where(User.id == user_id))
    user = query.scalar_one_or_none()
    
    if user is None or user.is_deleted or not user.is_active:
        logger.critical(f"🚨 Security Breach Blocked: Action attempted by shadow-state user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCOUNT_SUSPENDED"
        )
        
    return user