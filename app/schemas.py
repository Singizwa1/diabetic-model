"""
Pydantic validation schemas for Diabetes Risk Prediction System.

Schemas for:
- Authentication (register, login, tokens)
- User profiles
- Assessment sessions
- Daily logs
- Predictions
- Notifications
- Health checks
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum


class RiskLevelEnum(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SessionStatusEnum(str, Enum):
    """Session lifecycle statuses."""
    COLLECTING = "collecting"
    COMPLETED = "completed"
    PREDICTED = "predicted"
    CANCELLED = "cancelled"


# ==================== AUTH SCHEMAS ====================

class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Redis token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordResetRequest(BaseModel):
    """Request password reset by email."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token and new password."""
    token: str
    new_password: str = Field(..., min_length=8)


# ==================== USER SCHEMAS ====================

class UserResponse(BaseModel):
    """User response (safe to return to client)."""
    id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== PROFILE SCHEMAS ====================

class UserProfileRequest(BaseModel):
    """User profile creation/update request."""
    age: int = Field(..., ge=0, le=150)
    sex: str = Field(..., pattern="^(male|female)$")
    height_cm: float = Field(..., gt=0, le=300)
    weight_kg: float = Field(..., gt=0, le=500)


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: UUID
    user_id: UUID
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    bmi: float
    created_at: datetime
    updated_at: datetime
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== SESSION SCHEMAS ====================

class AssessmentSessionCreate(BaseModel):
    """Start a new assessment session."""
    profile_id: UUID
    target_days: int = Field(3, ge=1, le=30)


class DailyLogRequest(BaseModel):
    """Submit daily symptom log."""
    day_number: int = Field(..., ge=1, le=30)
    urination_frequency: int = Field(..., ge=0, le=30)
    thirst_frequency: int = Field(..., ge=0, le=30)
    thirst_level: int = Field(..., ge=1, le=4)
    fatigue_level: int = Field(..., ge=1, le=5)
    physical_activity: bool
    alcohol_consumption: bool
    smoking: bool


class DailyLogResponse(BaseModel):
    """Daily log response."""
    id: UUID
    session_id: UUID
    day_number: int
    log_date: datetime
    urination_frequency: int
    thirst_frequency: int
    thirst_level: int
    fatigue_level: int
    physical_activity: bool
    alcohol_consumption: bool
    smoking: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AssessmentSessionResponse(BaseModel):
    """Assessment session response."""
    id: UUID
    user_id: UUID
    profile_id: UUID
    status: SessionStatusEnum
    target_days: int
    started_at: datetime
    completed_at: Optional[datetime]
    daily_logs: List[DailyLogResponse] = []
    created_at: datetime
    updated_at: datetime
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== PREDICTION SCHEMAS ====================

class PredictionResponse(BaseModel):
    """Prediction result response."""
    id: UUID
    session_id: UUID
    user_id: UUID
    model_version: str
    probability: float
    risk_level: RiskLevelEnum
    feature_payload: Optional[dict]
    created_at: datetime
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class PredictionDetailedResponse(PredictionResponse):
    """Detailed prediction with session context."""
    session: AssessmentSessionResponse
    
    model_config = ConfigDict(from_attributes=True)


# ==================== MODEL REGISTRY SCHEMAS ====================

class ModelRegistryResponse(BaseModel):
    """Model registry entry response."""
    id: UUID
    model_version: str
    workflow_version: str
    artifact_path: str
    metrics: Optional[dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== NOTIFICATION SCHEMAS ====================

class NotificationResponse(BaseModel):
    """Notification response."""
    id: UUID
    user_id: UUID
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== HEALTH CHECK SCHEMAS ====================

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    api_version: str
    model_loaded: bool
    database_connected: bool
    redis_connected: bool
    timestamp: datetime


# ==================== TRAINING SCHEMAS ====================

class TrainingResultResponse(BaseModel):
    """Model training result response."""
    status: str
    model_version: str
    workflow_version: str
    metrics: Optional[dict]
    timestamp: str
    message: Optional[str] = None


class ModelInfoResponse(BaseModel):
    """Current model information."""
    version: str
    workflow: str
    metrics: Optional[dict]
    artifact_path: str
    is_active: bool
