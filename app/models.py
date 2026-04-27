"""
SQLAlchemy ORM Models for Diabetes Risk Prediction System.

Tables:
- users: User accounts and credentials
- user_profiles: Static health profiles
- assessment_sessions: 3-day assessment cycles
- daily_logs: Day-level symptom logs
- predictions: Risk prediction results
- notifications: User alerts
- model_registry: ML model tracking
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.database import Base


class RiskLevel(str, enum.Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SessionStatus(str, enum.Enum):
    """Session lifecycle statuses."""
    COLLECTING = "collecting"
    COMPLETED = "completed"
    PREDICTED = "predicted"
    CANCELLED = "cancelled"


class User(Base):
    """User account and authentication."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profiles = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("AssessmentSession", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    """Static health profile (age, weight, height, BMI)."""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    sex = Column(String(10), nullable=False)
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    bmi = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profiles")
    sessions = relationship("AssessmentSession", back_populates="profile", cascade="all, delete-orphan")


class AssessmentSession(Base):
    """One risk assessment cycle (typically 3 days)."""
    __tablename__ = "assessment_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False, index=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.COLLECTING, index=True)
    target_days = Column(Integer, default=3)
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    profile = relationship("UserProfile", back_populates="sessions")
    daily_logs = relationship("DailyLog", back_populates="session", cascade="all, delete-orphan")
    prediction = relationship("Prediction", back_populates="session", uselist=False, cascade="all, delete-orphan")


class DailyLog(Base):
    """Daily symptom log during assessment session."""
    __tablename__ = "daily_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("assessment_sessions.id"), nullable=False, index=True)
    day_number = Column(Integer, nullable=False)
    log_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Dynamic health inputs
    urination_frequency = Column(Integer, nullable=False)
    thirst_frequency = Column(Integer, nullable=False)
    thirst_level = Column(Integer, nullable=False)
    fatigue_level = Column(Integer, nullable=False)
    physical_activity = Column(Boolean, nullable=False)
    alcohol_consumption = Column(Boolean, nullable=False)
    smoking = Column(Boolean, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("AssessmentSession", back_populates="daily_logs")


class Prediction(Base):
    """Risk prediction result for completed session."""
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("assessment_sessions.id"), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    probability = Column(Float, nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False, index=True)
    feature_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    session = relationship("AssessmentSession", back_populates="prediction")
    user = relationship("User", back_populates="predictions")


class ModelRegistry(Base):
    """Track deployed ML models."""
    __tablename__ = "model_registry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    model_version = Column(String(50), unique=True, nullable=False, index=True)
    workflow_version = Column(String(50), nullable=False)
    artifact_path = Column(String(500), nullable=False)
    metrics = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Notification(Base):
    """In-app notifications (high risk alerts, etc)."""
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
