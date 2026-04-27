from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime
import numpy as np

from app.models import AssessmentSession, DailyLog, UserProfile, SessionStatus, Prediction, RiskLevel
from app.schemas import AssessmentSessionCreate, DailyLogRequest


class SessionService:
    """Service for managing assessment sessions and daily logs."""
    
    @staticmethod
    def create_session(db: Session, user_id: UUID, session_data: AssessmentSessionCreate) -> AssessmentSession:
        """
        Start a new assessment session.
        
        Args:
            db: Database session
            user_id: User ID
            session_data: Session creation data
        
        Returns:
            Created session
        
        Raises:
            HTTPException: If profile not found
        """
        # Verify profile exists and belongs to user
        profile = db.query(UserProfile).filter(
            UserProfile.id == session_data.profile_id,
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Create session
        session = AssessmentSession(
            user_id=user_id,
            profile_id=session_data.profile_id,
            status=SessionStatus.COLLECTING,
            target_days=session_data.target_days
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def add_daily_log(db: Session, user_id: UUID, session_id: UUID, log_data: DailyLogRequest) -> DailyLog:
        """
        Add a daily symptom log to a session.
        
        Args:
            db: Database session
            user_id: User ID (for authorization)
            session_id: Session ID
            log_data: Daily log data
        
        Returns:
            Created daily log
        
        Raises:
            HTTPException: If session not found or invalid
        """
        # Verify session exists and belongs to user
        session = db.query(AssessmentSession).filter(
            AssessmentSession.id == session_id,
            AssessmentSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if session.status != SessionStatus.COLLECTING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not accepting new logs"
            )
        
        # Check if log for this day already exists
        existing_log = db.query(DailyLog).filter(
            DailyLog.session_id == session_id,
            DailyLog.day_number == log_data.day_number
        ).first()
        
        if existing_log:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Log for day {log_data.day_number} already exists"
            )
        
        # Create daily log
        daily_log = DailyLog(
            session_id=session_id,
            day_number=log_data.day_number,
            urination_frequency=log_data.urination_frequency,
            thirst_frequency=log_data.thirst_frequency,
            thirst_level=log_data.thirst_level,
            fatigue_level=log_data.fatigue_level,
            physical_activity=log_data.physical_activity,
            alcohol_consumption=log_data.alcohol_consumption,
            smoking=log_data.smoking
        )
        
        db.add(daily_log)
        db.commit()
        db.refresh(daily_log)
        
        return daily_log
    
    @staticmethod
    def get_session(db: Session, user_id: UUID, session_id: UUID) -> AssessmentSession:
        """
        Get a session by ID (authorized to user).
        
        Args:
            db: Database session
            user_id: User ID (for authorization)
            session_id: Session ID
        
        Returns:
            Session
        
        Raises:
            HTTPException: If session not found
        """
        session = db.query(AssessmentSession).filter(
            AssessmentSession.id == session_id,
            AssessmentSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return session
    
    @staticmethod
    def get_user_sessions(db: Session, user_id: UUID, limit: int = 10) -> list[AssessmentSession]:
        """Get all sessions for a user, sorted by most recent."""
        return db.query(AssessmentSession).filter(
            AssessmentSession.user_id == user_id
        ).order_by(AssessmentSession.started_at.desc()).limit(limit).all()
    
    @staticmethod
    def complete_session(db: Session, user_id: UUID, session_id: UUID) -> AssessmentSession:
        """
        Mark a session as completed.
        
        Args:
            db: Database session
            user_id: User ID (for authorization)
            session_id: Session ID
        
        Returns:
            Updated session
        
        Raises:
            HTTPException: If session not found
        """
        session = SessionService.get_session(db, user_id, session_id)
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def cancel_session(db: Session, user_id: UUID, session_id: UUID) -> AssessmentSession:
        """Cancel a session."""
        session = SessionService.get_session(db, user_id, session_id)
        session.status = SessionStatus.CANCELLED
        
        db.commit()
        db.refresh(session)
        return session


class PredictionService:
    """Service for managing predictions."""

    @staticmethod
    def _json_safe(value):
        """Convert nested NumPy values and other non-JSON-native types to plain Python values."""
        if isinstance(value, dict):
            return {key: PredictionService._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [PredictionService._json_safe(item) for item in value]
        if isinstance(value, tuple):
            return [PredictionService._json_safe(item) for item in value]
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            return float(value)
        if isinstance(value, np.bool_):
            return bool(value)
        if isinstance(value, np.ndarray):
            return [PredictionService._json_safe(item) for item in value.tolist()]
        return value
    
    @staticmethod
    def create_prediction(
        db: Session,
        session_id: UUID,
        user_id: UUID,
        probability: float,
        model_version: str,
        feature_payload: dict = None
    ) -> Prediction:
        """
        Create a prediction record.
        
        Args:
            db: Database session
            session_id: Associated session ID
            user_id: User ID
            probability: Prediction probability (0-1)
            model_version: Version of model used
            feature_payload: Input features used for prediction
        
        Returns:
            Created prediction
        """
        # Determine risk level
        if probability < 0.3:
            risk_level = RiskLevel.LOW
        elif probability < 0.7:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH
        
        prediction = Prediction(
            session_id=session_id,
            user_id=user_id,
            model_version=model_version,
            probability=probability,
            risk_level=risk_level,
            feature_payload=PredictionService._json_safe(feature_payload) if feature_payload is not None else None
        )
        
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        
        return prediction
    
    @staticmethod
    def get_user_predictions(db: Session, user_id: UUID, limit: int = 10) -> list[Prediction]:
        """Get all predictions for a user, sorted by most recent."""
        return db.query(Prediction).filter(
            Prediction.user_id == user_id
        ).order_by(Prediction.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_latest_prediction(db: Session, user_id: UUID) -> Prediction:
        """Get the most recent prediction for a user."""
        prediction = db.query(Prediction).filter(
            Prediction.user_id == user_id
        ).order_by(Prediction.created_at.desc()).first()
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No predictions found for user"
            )
        
        return prediction
