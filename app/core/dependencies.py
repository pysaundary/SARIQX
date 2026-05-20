from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token
from loguru import logger

# Swagger UI aur API framework ko batata hai ki humein Bearer Token chahiye HTTP headers mein
security_scheme = HTTPBearer(auto_error=False) 

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """
    Strict Dependency Guard for Protected Routes.
    Validates the incoming JWT, unpacks tenant contexts, and stops unauthorized intrusions.
    """
    if not credentials:
        logger.warning("🛡️ Auth Dependency Guard: Intercepted request with missing Authorization header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are missing. Access Denied.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = credentials.credentials
    try:
        # Cryptographically decode using our core security engine
        payload = decode_token(token)
        
        # Guard ensure karega ki refresh token ko koi access token ki jagah misuse na kare
        if payload.get("type") != "access":
            raise ValueError("Invalid token type context parsed.")
            
        return payload # Returns the clean decrypted dict containing user_id, tenant_id, role etc.
        
    except ValueError as err:
        logger.error(f"🛡️ Auth Dependency Guard: Signatures verification failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )