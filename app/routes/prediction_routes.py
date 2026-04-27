from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas import PredictionResponse, PredictionDetailedResponse
from app.services.session_service import PredictionService, SessionService
from app.models import Prediction
from app.services.ml_service import MLService
from app.services.email_service import EmailService
from app.core.security import get_current_user
from app.models import SessionStatus, RiskLevel

router = APIRouter()


@router.post("/sessions/{session_id}/predict", response_model=PredictionResponse)
def predict_session_risk(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run diabetes risk prediction for a completed session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Prediction result
    """
    from uuid import UUID as UUID_type
    user_id = UUID(current_user.get("user_id"))
    
    # Get session and profile
    session = SessionService.get_session(db, user_id, session_id)
    
    if session.status != SessionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session must be completed before making prediction"
        )
    
    # Get user profile
    profile = session.profile
    
    # Make prediction
    try:
        probability, feature_payload = MLService.predict_session_risk(db, session, profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Prevent duplicate predictions for the same session
    existing = db.query(Prediction).filter(Prediction.session_id == session_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A prediction already exists for this session. Start a new session to run another prediction."
        )

    # Create prediction record
    prediction = PredictionService.create_prediction(
        db,
        session_id=session_id,
        user_id=user_id,
        probability=probability,
        model_version="mobile_session_v1",
        feature_payload=feature_payload
    )
    
    # Update session status
    session.status = SessionStatus.PREDICTED
    db.commit()
    
    # Get user email for notifications
    user = session.user
    
    risk_label = prediction.risk_level.value if hasattr(prediction.risk_level, "value") else str(prediction.risk_level)

    # Send recommendation email for every completed assessment
    EmailService.send_assessment_result_email(
        email=user.email,
        user_name=user.full_name or user.email,
        probability=probability,
        risk_level=risk_label,
    )

    # Create in-app notification for every completed assessment
    if prediction.risk_level == RiskLevel.HIGH:
        notification_title = "⚠️ High Risk Alert"
        notification_message = f"Your diabetes risk assessment shows a HIGH RISK result ({probability:.1%})."
        notification_type = "risk_alert"
    else:
        notification_title = "Assessment Complete"
        notification_message = f"Your diabetes risk assessment is complete. Risk level: {risk_label.upper()}"
        notification_type = "assessment_complete"

    EmailService.create_in_app_notification(
        db,
        user_id=user_id,
        title=notification_title,
        message=notification_message,
        notification_type=notification_type,
    )
    
    response = PredictionResponse.model_validate(prediction).model_dump()
    response["message"] = "Prediction generated successfully and sent to the user"
    return response


@router.get("/latest", response_model=PredictionResponse)
def get_latest_prediction(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the most recent prediction for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Latest prediction
    """
    user_id = UUID(current_user.get("user_id"))
    prediction = PredictionService.get_latest_prediction(db, user_id)
    return prediction


@router.get("", response_model=list[PredictionDetailedResponse])
def get_user_predictions(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all predictions for the current user.
    
    Args:
        limit: Maximum number of predictions to return
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of predictions with session context
    """
    user_id = UUID(current_user.get("user_id"))
    predictions = PredictionService.get_user_predictions(db, user_id, limit)
    return predictions
