from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UserResponse, ModelRegistryResponse
from app.core.security import get_current_admin_user
from app.models import User, ModelRegistry

router = APIRouter()


@router.get("/users", response_model=list[UserResponse])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all users (admin only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_admin: Current admin user
        db: Database session
    
    Returns:
        List of all users
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


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
    
    total_predictions = db.query(Prediction).count()
    high_risk_predictions = db.query(Prediction).filter(
        Prediction.risk_level == RiskLevel.HIGH
    ).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_predictions": total_predictions,
        "high_risk_predictions": high_risk_predictions,
        "high_risk_percentage": (high_risk_predictions / total_predictions * 100) if total_predictions > 0 else 0
    }
