import joblib
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models import DailyLog, UserProfile, AssessmentSession, ModelRegistry

logger = logging.getLogger(__name__)


class MLService:
    """Service for ML model loading and predictions."""
    
    # Singleton model cache
    _model = None
    _model_version = None

    @staticmethod
    def _to_json_safe(value):
        """Convert NumPy and other non-JSON-native values to plain Python types."""
        if isinstance(value, dict):
            return {key: MLService._to_json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [MLService._to_json_safe(item) for item in value]
        if isinstance(value, tuple):
            return [MLService._to_json_safe(item) for item in value]
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            return float(value)
        if isinstance(value, np.bool_):
            return bool(value)
        if isinstance(value, np.ndarray):
            return [MLService._to_json_safe(item) for item in value.tolist()]
        return value
    
    @staticmethod
    def load_model(model_path: str = "saved_model/model.pkl") -> Tuple[object, str]:
        """
        Load ML model from disk (with caching).
        
        Args:
            model_path: Path to saved model
        
        Returns:
            Tuple of (model, model_version)
        """
        try:
            if MLService._model is None:
                if not Path(model_path).exists():
                    logger.warning(f"Model not found at {model_path}")
                    return None, "not_loaded"
                
                MLService._model = joblib.load(model_path)
                MLService._model_version = "mobile_session_v1"
                logger.info(f"Model loaded from {model_path}")
            
            return MLService._model, MLService._model_version
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return None, "error"
    
    @staticmethod
    def predict_session_risk(
        db: Session,
        session: AssessmentSession,
        profile: UserProfile
    ) -> Tuple[float, dict]:
        """
        Predict diabetes risk for a session using aggregated daily logs.
        
        Args:
            db: Database session
            session: AssessmentSession instance
            profile: UserProfile instance
        
        Returns:
            Tuple of (probability, feature_dict)
        
        Raises:
            ValueError: If session doesn't have enough daily logs
        """
        # Get daily logs
        daily_logs = db.query(DailyLog).filter(
            DailyLog.session_id == session.id
        ).order_by(DailyLog.day_number).all()
        
        if not daily_logs:
            raise ValueError("No daily logs found for session")
        
        # Aggregate features from daily logs
        features = MLService._aggregate_session_features(daily_logs, profile)
        
        # Load model
        model, model_version = MLService.load_model()
        
        if model is None:
            # Fallback to rule-based scoring
            logger.warning("Model not available, using rule-based scoring")
            probability = MLService._rule_based_scoring(features)
            return probability, features
        
        # Prepare feature vector
        feature_vector = MLService._prepare_feature_vector(features)
        
        # Make prediction
        try:
            probability = float(model.predict_proba(feature_vector)[0][1])
            logger.info(f"Prediction made: {probability:.4f}")
            return probability, features
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            # Fallback to rule-based
            probability = MLService._rule_based_scoring(features)
            return probability, features
    
    @staticmethod
    def _aggregate_session_features(daily_logs: list, profile: UserProfile) -> dict:
        """
        Aggregate daily logs into session-level features.
        
        Args:
            daily_logs: List of DailyLog objects
            profile: UserProfile object
        
        Returns:
            Dictionary of aggregated features
        """
        if not daily_logs:
            raise ValueError("No daily logs to aggregate")
        
        # Extract values
        urination_freqs = [log.urination_frequency for log in daily_logs]
        thirst_freqs = [log.thirst_frequency for log in daily_logs]
        thirst_levels = [log.thirst_level for log in daily_logs]
        fatigue_levels = [log.fatigue_level for log in daily_logs]
        physical_activities = [1 if log.physical_activity else 0 for log in daily_logs]
        alcohol_consumptions = [1 if log.alcohol_consumption else 0 for log in daily_logs]
        smokings = [1 if log.smoking else 0 for log in daily_logs]
        
        # Aggregate
        features = {
            # Static profile
            "age": profile.age,
            "sex": 1 if profile.sex.lower() == "male" else 0,
            "bmi": profile.bmi,
            
            # Dynamic aggregates
            "urination_frequency_mean": np.mean(urination_freqs),
            "urination_frequency_max": np.max(urination_freqs),
            "thirst_frequency_mean": np.mean(thirst_freqs),
            "thirst_frequency_max": np.max(thirst_freqs),
            "thirst_level_mean": np.mean(thirst_levels),
            "thirst_level_max": np.max(thirst_levels),
            "fatigue_level_mean": np.mean(fatigue_levels),
            "fatigue_level_max": np.max(fatigue_levels),
            "physical_activity_count": np.sum(physical_activities),
            "alcohol_consumption_count": np.sum(alcohol_consumptions),
            "smoking": np.max(smokings),  # If smokes at least once
            "days_logged": len(daily_logs)
        }
        
        return MLService._to_json_safe(features)
    
    @staticmethod
    def _prepare_feature_vector(features: dict) -> np.ndarray:
        """
        Prepare feature vector for model prediction.
        
        Args:
            features: Dictionary of features
        
        Returns:
            Feature vector as numpy array
        """
        feature_order = [
            "age", "sex", "bmi",
            "urination_frequency_mean", "urination_frequency_max",
            "thirst_frequency_mean", "thirst_frequency_max",
            "thirst_level_mean", "thirst_level_max",
            "fatigue_level_mean", "fatigue_level_max",
            "physical_activity_count", "alcohol_consumption_count", "smoking",
            "days_logged"
        ]
        
        vector = [features.get(key, 0) for key in feature_order]
        return np.array(vector).reshape(1, -1)
    
    @staticmethod
    def _rule_based_scoring(features: dict) -> float:
        """
        Fallback rule-based scoring when model is unavailable.
        
        Args:
            features: Dictionary of aggregated features
        
        Returns:
            Risk probability (0-1)
        """
        score = 0.0
        
        # High thirst and urination are strong indicators
        if features.get("thirst_frequency_mean", 0) > 3:
            score += 0.3
        if features.get("urination_frequency_mean", 0) > 5:
            score += 0.3
        
        # Fatigue
        if features.get("fatigue_level_mean", 0) > 3:
            score += 0.15
        
        # BMI
        bmi = features.get("bmi", 0)
        if bmi > 30:
            score += 0.15
        elif bmi > 25:
            score += 0.1
        
        # Age (diabetes more common in older)
        age = features.get("age", 0)
        if age > 50:
            score += 0.1
        
        # Lifestyle
        activity_count = features.get("physical_activity_count", 0)
        days = features.get("days_logged", 1)
        if activity_count == 0:  # No activity
            score += 0.1
        
        if features.get("alcohol_consumption_count", 0) > days / 2:
            score += 0.05
        
        return min(score, 1.0)
