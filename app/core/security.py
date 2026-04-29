from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.cache import TokenManager, RedisUnavailableError
from app.core.config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, email: str, is_admin: bool) -> tuple[str, int]:
    """Create JWT and store its session payload in Redis keyed by JTI."""
    expires_in = int(settings.JWT_EXPIRES_HOURS) * 60 * 60
    expire_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    jti = str(uuid4())
    role = "admin" if is_admin else "user"

    payload = {
        "id": user_id,
        "email": email,
        "role": role,
        "is_admin": is_admin,
        "jti": jti,
        "exp": expire_at,
    }

    secret = settings.JWT_SECRET or settings.SECRET_KEY
    token = jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)

    redis_payload = {
        "id": user_id,
        "email": email,
        "role": role,
        "is_admin": is_admin,
        "jti": jti,
    }
    try:
        TokenManager.store_session(jti=jti, token_payload=redis_payload, ttl_seconds=expires_in)
    except RedisUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        ) from exc

    return token, expires_in


def verify_token(token: str) -> dict:
    """Verify JWT, ensure session exists in Redis, and enforce blacklist."""
    secret = settings.JWT_SECRET or settings.SECRET_KEY

    try:
        if TokenManager.is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been blacklisted",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except RedisUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    try:
        decoded = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    jti = decoded.get("jti")
    try:
        if not jti or not TokenManager.is_session_active(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token not found in Redis - may have been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except RedisUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return {
        "user_id": decoded.get("id"),
        "email": decoded.get("email"),
        "role": decoded.get("role"),
        "is_admin": bool(decoded.get("is_admin", False)),
        "jti": jti,
    }


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to extract and verify current user from Redis token.
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        User data from token (user_id, is_admin)
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    return verify_token(token)


async def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to ensure current user is an admin.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current user if they are admin
    
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
