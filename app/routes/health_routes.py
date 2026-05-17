from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.schemas import NotificationResponse, HealthCheckResponse
from app.core.security import get_current_user
from app.services.email_service import EmailService
from app.services.ml_service import MLService
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


# ==================== ROOT ENTRY POINT ====================

@router.get("/", tags=["Root"])
def root():
    """
    Welcome endpoint - root path.
    
    Returns:
        API information and documentation links
    """
    return {
        "message": "Welcome to Diabetes Risk Prediction API",
     
    }


# ==================== NOTIFICATIONS ====================

@router.get("/notifications", response_model=list[NotificationResponse])
def get_notifications(
    unread_only: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user notifications.
    
    Args:
        unread_only: If True, return only unread notifications
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of notifications
    """
    user_id = UUID(current_user.get("user_id"))
    notifications = EmailService.get_user_notifications(db, user_id, unread_only)
    return notifications


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a notification as read.
    
    Args:
        notification_id: Notification ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Updated notification
    """
    user_id = UUID(current_user.get("user_id"))
    try:
        notification = EmailService.mark_notification_as_read(db, notification_id, user_id)
        return {"id": notification.id, "is_read": notification.is_read}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== HEALTH CHECK ====================

@router.get("/health", response_model=HealthCheckResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Args:
        db: Database session
    
    Returns:
        Health status
    """
    try:
        # Check database connection
        db.execute("SELECT 1")
        db_connected = True
    except Exception:
        db_connected = False
    
    # Check if model is loaded
    _, model_version = MLService.load_model()
    model_loaded = model_version != "not_loaded"
    
    return HealthCheckResponse(
        status="ok" if db_connected else "degraded",
        api_version="2.0.0",
        model_loaded=model_loaded,
        database_connected=db_connected,
        timestamp=datetime.utcnow()
    )
