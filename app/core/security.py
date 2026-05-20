from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from bcrypt import hashpw, gensalt, checkpw
from app.core.collector import collector
from loguru import logger

# Helper functions to safely extract JWT configs from Pydantic Matrix via Collector
def _get_jwt_secret() -> str:
    return collector.get("JWT_SECRET_KEY", "SARIQX_EMERGENCY_FALLBACK_2026")

def _get_jwt_algorithm() -> str:
    return collector.get("JWT_ALGORITHM", "HS256")


# ==============================================================================
# 🔐 SECTION 1: CRYO-PASSWORD HASHING DRIVERS (Bcrypt Native)
# ==============================================================================

def hash_password(password: str) -> str:
    """
    Plain-text password ko adaptive work-factor ke sath secure multi-hash blob mein badalna.
    """
    pwd_bytes = password.encode('utf-8')
    # gensalt() default rounds=12 hold karta hai jo hardware performance ke liye optimal hai
    hashed = hashpw(pwd_bytes, gensalt())
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Incoming plain string aur database ke encrypted secure hash ko compare karna.
    """
    try:
        return checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"🛡️ Cryptographic identification failure during password matching: {e}")
        return False


# ==============================================================================
# 🎫 SECTION 2: TOKEN GENERATION LIFE-CYCLE (Access / Refresh Matrices)
# ==============================================================================

def create_access_token(payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    O(1) look-up capability ke sath short-lived Access Token compile karna.
    """
    to_encode = payload.copy()
    
    # Expiry time calculate karo current timezone-aware UTC format mein
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        minutes = collector.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
        expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    
    # Token metadata payloads injected strictly
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc) # Issued At Time
    })
    
    encoded_jwt = jwt.encode(to_encode, _get_jwt_secret(), algorithm=_get_jwt_algorithm())
    return encoded_jwt


def create_refresh_token(payload: Dict[str, Any]) -> str:
    """
    Long-term session persistence ke liye unique cryptographically signed Refresh Token banana.
    """
    to_encode = payload.copy()
    
    days = collector.get("REFRESH_TOKEN_EXPIRE_DAYS", 7)
    expire = datetime.now(timezone.utc) + timedelta(days=days)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc)
    })
    
    encoded_jwt = jwt.encode(to_encode, _get_jwt_secret(), algorithm=_get_jwt_algorithm())
    return encoded_jwt


# ==============================================================================
# 🎯 SECTION 3: TOKEN DECODING & SIGNATURE VALIDATION
# ==============================================================================

def decode_token(token: str) -> Dict[str, Any]:
    """
    Incoming Bearer token ke signatures verify aur decode karna.
    Throws structural errors agar token expired ya tampered ho.
    """
    try:
        decoded_payload = jwt.decode(
            token, 
            _get_jwt_secret(), 
            algorithms=[_get_jwt_algorithm()]
        )
        return decoded_payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("🎫 Token Verification Block: Passed token string has expired signature bounds.")
        raise ValueError("Token signature has expired.")
        
    except jwt.InvalidTokenError as err:
        logger.error(f"🚫 Token Interception Security Alert: Invalid token parsing attempt detected: {err}")
        raise ValueError("Cryptographic verification failed. Token is corrupted or malicious.")