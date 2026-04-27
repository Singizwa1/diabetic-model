from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas import (
    AssessmentSessionCreate,
    AssessmentSessionResponse,
    DailyLogRequest,
    DailyLogResponse
)
from app.services.session_service import SessionService
from app.core.security import get_current_user

router = APIRouter()


@router.post("", response_model=AssessmentSessionResponse)
def create_session(
    session_data: AssessmentSessionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a new assessment session.
    
    Args:
        session_data: Session creation data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created session
    """
    user_id = UUID(current_user.get("user_id"))
    session = SessionService.create_session(db, user_id, session_data)
    response = AssessmentSessionResponse.model_validate(session).model_dump()
    response["message"] = "Assessment session created successfully"
    return response


@router.get("", response_model=list[AssessmentSessionResponse])
def get_user_sessions(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all sessions for the current user.
    
    Args:
        limit: Maximum number of sessions to return
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of sessions
    """
    user_id = UUID(current_user.get("user_id"))
    sessions = SessionService.get_user_sessions(db, user_id, limit)
    return sessions


@router.get("/{session_id}", response_model=AssessmentSessionResponse)
def get_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Session details with all daily logs
    """
    user_id = UUID(current_user.get("user_id"))
    session = SessionService.get_session(db, user_id, session_id)
    return session


@router.post("/{session_id}/daily-logs", response_model=DailyLogResponse)
def add_daily_log(
    session_id: UUID,
    log_data: DailyLogRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a daily symptom log to a session.
    
    Args:
        session_id: Session ID
        log_data: Daily log data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created daily log
    """
    user_id = UUID(current_user.get("user_id"))
    daily_log = SessionService.add_daily_log(db, user_id, session_id, log_data)
    response = DailyLogResponse.model_validate(daily_log).model_dump()
    response["message"] = "Daily log created successfully"
    return response


@router.get("/{session_id}/daily-logs", response_model=list[DailyLogResponse])
def get_session_logs(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all daily logs for a session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of daily logs
    """
    user_id = UUID(current_user.get("user_id"))
    session = SessionService.get_session(db, user_id, session_id)
    return session.daily_logs


@router.post("/{session_id}/complete", response_model=AssessmentSessionResponse)
def complete_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a session as completed.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Updated session
    """
    user_id = UUID(current_user.get("user_id"))
    session = SessionService.complete_session(db, user_id, session_id)
    response = AssessmentSessionResponse.model_validate(session).model_dump()
    response["message"] = "Assessment session completed successfully"
    return response


@router.post("/{session_id}/cancel", response_model=AssessmentSessionResponse)
def cancel_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Updated session
    """
    user_id = UUID(current_user.get("user_id"))
    session = SessionService.cancel_session(db, user_id, session_id)
    response = AssessmentSessionResponse.model_validate(session).model_dump()
    response["message"] = "Assessment session cancelled successfully"
    return response
