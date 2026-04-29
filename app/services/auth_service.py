from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from uuid import UUID
import jwt
from jwt import InvalidTokenError
from datetime import datetime, timedelta, timezone
import random

from app.models import User
from app.schemas import UserRegister, UserLogin, TokenResponse, PasswordResetVerify
from app.core.security import hash_password, verify_password, create_access_token
from app.cache import TokenManager, redis_client, RedisUnavailableError
from app.services.email_service import EmailService
from app.core.config import get_settings

settings = get_settings()


class AuthService:
    """Authentication service using Redis tokens."""
    
    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> User:
        """
        Register a new user.
        
        Args:
            db: Database session
            user_data: Registration data
        
        Returns:
            Created user
        
        Raises:
            HTTPException: If email already exists
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name
        )
        
        try:
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creating user"
            )
    
    @staticmethod
    def login_user(db: Session, login_data: UserLogin) -> TokenResponse:
        """
        Authenticate user and return Redis token.
        
        Args:
            db: Database session
            login_data: Login credentials
        
        Returns:
            Token response
        
        Raises:
            HTTPException: If credentials are invalid
        """
        # Find user by email
        user = db.query(User).filter(User.email == login_data.email).first()
        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Create JWT and persist JTI session in Redis
        token, expires_in = create_access_token(
            user_id=str(user.id),
            email=user.email,
            is_admin=user.is_admin,
        )
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
        )
    
    @staticmethod
    def logout_user(token: str) -> bool:
        """
        Logout user by revoking token.
        
        Args:
            token: Token string
        
        Returns:
            True if logged out
        """
        # Blacklist full token immediately
        try:
            TokenManager.blacklist_token(token)
        except RedisUnavailableError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable"
            )

        # Remove associated session by JTI if token can be decoded
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            jti = decoded.get("jti")
            if jti:
                try:
                    TokenManager.remove_session(jti)
                except RedisUnavailableError:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Authentication service temporarily unavailable"
                    )
        except InvalidTokenError:
            pass

        return True
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> User:
        """Get user by ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    @staticmethod
    def request_password_reset(db: Session, email: str) -> bool:
        """Generate a 6-digit OTP, store in Redis, and email it to the user."""
        user = db.query(User).filter(User.email == email).first()
        # Always return success response to avoid user enumeration
        if not user:
            return True

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Store OTP in Redis: resetCode:{otp} -> email for 5 minutes
        redis_key = f"resetCode:{otp}"
        try:
            redis_client.setex(redis_key, 300, user.email)
        except Exception:
            # If Redis fails, still avoid leaking info
            return True

        # Send email with OTP in place of reset link
        EmailService.send_password_reset_email(user.email, user.full_name or user.email, otp)
        return True

    @staticmethod
    def verify_otp(db: Session, otp: str) -> bool:
        """Verify the OTP and create a reset session in Redis."""
        redis_key = f"resetCode:{otp}"
        email = None
        try:
            email = redis_client.get(redis_key)
        except Exception:
            pass

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )

        # Create reset session: resetSession:{email} -> email for 10 minutes
        session_key = f"resetSession:{email}"
        try:
            redis_client.setex(session_key, 600, email)
            redis_client.delete(redis_key)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

        return True

    @staticmethod
    def reset_password(db: Session, new_password: str) -> bool:
        """Reset password using active resetSession in Redis (no token)."""
        # Find any resetSession key
        try:
            keys = redis_client.keys("resetSession:*")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

        if not keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active reset session"
            )

        # Use the first session key
        session_key = keys[0]
        email = redis_client.get(session_key)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset session expired or invalid"
            )

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.password_hash = hash_password(new_password)
        db.add(user)
        db.commit()

        # Remove the reset session
        redis_client.delete(session_key)

        return True
