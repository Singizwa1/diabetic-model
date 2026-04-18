from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Sex = Literal["male", "female", "other"]
RiskLevel = Literal["Low", "Medium", "High"]
SessionStatus = Literal["collecting", "ready_for_prediction", "completed"]


class UserProfileRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    age: int = Field(..., ge=1, le=120)
    bmi: float = Field(..., gt=0)
    sex: Sex


class UserProfileResponse(BaseModel):
    status: Literal["success"]
    profile_saved: bool
    user_id: str
    updated_at: datetime


ProfileResponse = UserProfileResponse


class StartSessionRequest(BaseModel):
    user_id: str = Field(..., min_length=1)


class StartSessionResponse(BaseModel):
    session_id: str
    user_id: str
    status: SessionStatus
    days_required: int = 3
    days_received: int
    created_at: datetime


class DailyLogRequest(BaseModel):
    day: int = Field(..., ge=1, le=3)
    urination_frequency: int = Field(..., ge=0)
    thirst_frequency: int = Field(..., ge=0)
    thirst_level: int = Field(..., ge=1, le=4)
    fatigue_level: int = Field(..., ge=1, le=5)
    physical_activity: bool
    alcohol_consumption: bool
    smoking: bool


class DailyLogResponse(BaseModel):
    status: Literal["success"]
    session_id: str
    day: int
    days_received: int
    days_remaining: int
    session_complete: bool


class SessionStatusResponse(BaseModel):
    session_id: str
    user_id: str
    status: SessionStatus
    days_required: int = 3
    days_received: int
    days_remaining: int
    session_complete: bool


class PredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    session_id: str
    user_id: str
    risk_level: RiskLevel
    probability: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    prediction_time: datetime
    explanation: list[str]


class LatestPredictionResponse(BaseModel):
    user_id: str
    session_id: str
    risk_level: RiskLevel
    probability: float = Field(..., ge=0.0, le=1.0)
    predicted_at: datetime


class TrainingDataRequest(BaseModel):
    user_id: str
    session_id: str
    age: int = Field(..., ge=1, le=120)
    bmi: float = Field(..., gt=0)
    sex: Sex
    day_logs: list[DailyLogRequest]
    diabetes: int = Field(..., ge=0, le=1)


class TrainingDataResponse(BaseModel):
    status: Literal["success"]
    record_saved: bool


class RetrainRequest(BaseModel):
    force: bool = False
