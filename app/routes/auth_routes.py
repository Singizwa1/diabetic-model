import html

from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse

from app.database import get_db
from app.schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetVerify,
    PasswordResetLinkResponse,
    PasswordResetConfirmResponse,
)
from app.services.auth_service import AuthService
from app.core.security import get_current_user, security

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Args:
        user_data: Registration data (email, password, full_name)
        db: Database session
    
    Returns:
        Created user
    """
    user = AuthService.register_user(db, user_data)
    return user


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return JWT token.
    
    Args:
        login_data: Login credentials (email, password)
        db: Database session
    
    Returns:
        JWT token and metadata
    """
    token_response = AuthService.login_user(db, login_data)
    return token_response


@router.post("/logout")
def logout(
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Logout user by blacklisting token and removing active Redis session.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Success message
    """
    AuthService.logout_user(credentials.credentials)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get current authenticated user info.
    
    Args:
        current_user: Current user from token
        db: Database session
    
    Returns:
        User information
    """
    from uuid import UUID
    user = AuthService.get_user_by_id(db, UUID(current_user.get("user_id")))
    return user


@router.post("/password-reset", response_model=PasswordResetLinkResponse)
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Request a password reset OTP. A one-time code will be emailed if the account exists.
    """
    AuthService.request_password_reset(db, request.email)
    return {"message": "If an account with that email exists, a password reset code has been sent."}


@router.post("/password-reset/verify")
def verify_password_reset(verify: PasswordResetVerify, db: Session = Depends(get_db)):
    """
    Verify an OTP code sent to the user's email. On success a short reset session is created.
    """
    AuthService.verify_otp(db, verify.otp)
    return {"message": "OTP verified. You may now submit a new password."}


@router.post("/password-reset/confirm", response_model=PasswordResetConfirmResponse)
def complete_password_reset(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Complete password reset by providing a new password. Requires a prior successful OTP verification.
    """
    AuthService.reset_password(db, request.new_password)
    return {"message": "Password has been reset successfully."}



