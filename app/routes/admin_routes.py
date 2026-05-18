from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UserResponse, ModelRegistryResponse
from app.core.security import get_current_admin_user
from app.models import User, ModelRegistry
from app.models import Prediction, AssessmentSession, RiskLevel, SessionStatus
from app.schemas import PredictionResponse, AssessmentSessionResponse
from typing import Optional
from datetime import datetime

router = APIRouter()


@router.put("/users/{user_id}/toggle-admin")
def toggle_user_admin_status(
    user_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Toggle admin status for a user (admin only).
    
    Args:
        user_id: User ID
        current_admin: Current admin user
        db: Database session
    
    Returns:
        Updated user
    """
    from uuid import UUID
    
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_admin = not user.is_admin
    db.commit()
    db.refresh(user)
    
    return {"user_id": user_id, "is_admin": user.is_admin}


@router.put("/users/{user_id}/toggle-active")
def toggle_user_active_status(
    user_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Disable/enable a user account (admin only).
    
    Args:
        user_id: User ID
        current_admin: Current admin user
        db: Database session
    
    Returns:
        Updated user status
    """
    from uuid import UUID
    
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    return {"user_id": user_id, "is_active": user.is_active}


@router.get("/models", response_model=list[ModelRegistryResponse])
def get_model_registry(
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get model registry entries (admin only).
    
    Args:
        current_admin: Current admin user
        db: Database session
    
    Returns:
        List of registered models
    """
    models = db.query(ModelRegistry).order_by(ModelRegistry.created_at.desc()).all()
    return models


@router.get("/predictions", response_model=list[PredictionResponse])
def get_all_predictions(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get predictions across users with optional filters.
    """
    query = db.query(Prediction)

    if user_id:
        from uuid import UUID
        query = query.filter(Prediction.user_id == UUID(user_id))

    if risk_level:
        try:
            rl = RiskLevel(risk_level)
            query = query.filter(Prediction.risk_level == rl)
        except Exception:
            pass

    if from_date:
        query = query.filter(Prediction.created_at >= from_date)

    if to_date:
        query = query.filter(Prediction.created_at <= to_date)

    preds = query.order_by(Prediction.created_at.desc()).offset(skip).limit(limit).all()
    return preds


@router.get("/sessions", response_model=list[AssessmentSessionResponse])
def get_all_sessions(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get assessment sessions across users with optional filters.
    """
    query = db.query(AssessmentSession)

    if user_id:
        from uuid import UUID
        query = query.filter(AssessmentSession.user_id == UUID(user_id))

    if status:
        try:
            st = SessionStatus(status)
            query = query.filter(AssessmentSession.status == st)
        except Exception:
            pass

    if from_date:
        query = query.filter(AssessmentSession.started_at >= from_date)

    if to_date:
        query = query.filter(AssessmentSession.started_at <= to_date)

    sessions = query.order_by(AssessmentSession.started_at.desc()).offset(skip).limit(limit).all()
    return sessions


@router.get("/users", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    List users with optional search and filters.
    """
    query = db.query(User)

    if search:
        like = f"%{search}%"
        query = query.filter((User.email.ilike(like)) | (User.full_name.ilike(like)))

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if is_admin is not None:
        query = query.filter(User.is_admin == is_admin)

    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return users


@router.get("/statistics")
def get_admin_statistics(
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get system-wide statistics (admin only).
    
    Args:
        current_admin: Current admin user
        db: Database session
    
    Returns:
        System statistics
    """
    from app.models import Prediction, RiskLevel
    
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    total_sessions = db.query(AssessmentSession).count()
    active_sessions = db.query(AssessmentSession).filter(AssessmentSession.status == SessionStatus.COLLECTING).count()

    total_predictions = db.query(Prediction).count()
    high_risk_predictions = db.query(Prediction).filter(
        Prediction.risk_level == RiskLevel.HIGH
    ).count()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "total_predictions": total_predictions,
        "high_risk_predictions": high_risk_predictions,
        "high_risk_percentage": (high_risk_predictions / total_predictions * 100) if total_predictions > 0 else 0
    }


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_detail(
    user_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get user details by ID (admin only)."""
    from uuid import UUID

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
def get_prediction_detail(
    prediction_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get prediction detail by ID (admin only)."""
    from uuid import UUID

    pred = db.query(Prediction).filter(Prediction.id == UUID(prediction_id)).first()
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    return pred


@router.get("/sessions/{session_id}", response_model=AssessmentSessionResponse)
def get_session_detail(
    session_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get assessment session detail by ID (admin only)."""
    from uuid import UUID

    sess = db.query(AssessmentSession).filter(AssessmentSession.id == UUID(session_id)).first()
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return sess
