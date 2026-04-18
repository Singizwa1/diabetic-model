from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4

import numpy as np
import pandas as pd

from app.mobile_training import MODEL_PATH, SESSION_FEATURE_COLUMNS, load_model_artifact
from app.schemas import DailyLogRequest
from app.utils import map_probability_to_risk

DAYS_REQUIRED = 3
MODEL_VERSION = "mobile_session_v1"
_MODEL_CACHE: Optional[Dict[str, Any]] = None


@dataclass
class DailyLog:
    day: int
    urination_frequency: int
    thirst_frequency: int
    thirst_level: int
    fatigue_level: int
    physical_activity: bool
    alcohol_consumption: bool
    smoking: bool
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Profile:
    user_id: str
    age: int
    bmi: float
    sex: str
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Session:
    session_id: str
    user_id: str
    status: str = "collecting"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    daily_logs: Dict[int, DailyLog] = field(default_factory=dict)
    prediction: Optional[Dict[str, Any]] = None

    @property
    def days_received(self) -> int:
        return len(self.daily_logs)

    @property
    def days_remaining(self) -> int:
        return max(0, DAYS_REQUIRED - self.days_received)

    @property
    def session_complete(self) -> bool:
        return self.prediction is not None


PROFILES: Dict[str, Profile] = {}
SESSIONS: Dict[str, Session] = {}
PREDICTIONS: List[Dict[str, Any]] = []
TRAINING_DATA: List[Dict[str, Any]] = []
LOCK = Lock()


def create_or_update_profile(user_id: str, age: int, bmi: float, sex: str) -> Profile:
    profile = Profile(user_id=user_id, age=age, bmi=bmi, sex=sex)
    with LOCK:
        PROFILES[user_id] = profile
    return profile


def start_session(user_id: str) -> Session:
    if user_id not in PROFILES:
        raise ValueError("Profile not found. Create profile before starting a session.")

    session = Session(session_id=str(uuid4()), user_id=user_id)
    with LOCK:
        SESSIONS[session.session_id] = session
    return session


def add_daily_log(session_id: str, payload: DailyLogRequest) -> Session:
    with LOCK:
        session = SESSIONS.get(session_id)
        if session is None:
            raise ValueError("Session not found.")

        if session.session_complete:
            raise ValueError("Session already completed.")

        expected_day = session.days_received + 1
        if payload.day != expected_day:
            raise ValueError(f"Expected day {expected_day}, received day {payload.day}.")

        session.daily_logs[payload.day] = DailyLog(**payload.model_dump())
        session.status = "ready_for_prediction" if session.days_received == DAYS_REQUIRED else "collecting"
        return session


def get_session(session_id: str) -> Session:
    with LOCK:
        session = SESSIONS.get(session_id)
        if session is None:
            raise ValueError("Session not found.")
        return session


def _ordered_logs(session: Session) -> List[DailyLog]:
    return [session.daily_logs[day] for day in sorted(session.daily_logs.keys())]


def _slope(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=float)
    y = np.asarray(values, dtype=float)
    slope, _ = np.polyfit(x, y, 1)
    return float(slope)


def _series_metrics(values: List[float]) -> Dict[str, float]:
    arr = np.asarray(values, dtype=float)
    return {
        "mean": float(arr.mean()),
        "max": float(arr.max()),
        "slope": _slope(values),
    }


def build_session_features(session: Session) -> Dict[str, float]:
    profile = PROFILES.get(session.user_id)
    if profile is None:
        raise ValueError("Profile not found for session user.")

    logs = _ordered_logs(session)
    if len(logs) != DAYS_REQUIRED:
        raise ValueError("Prediction requires 3 completed daily logs.")

    urination = [log.urination_frequency for log in logs]
    thirst_frequency = [log.thirst_frequency for log in logs]
    thirst_level = [log.thirst_level for log in logs]
    fatigue_level = [log.fatigue_level for log in logs]
    inactive_days = [not log.physical_activity for log in logs]
    alcohol_days = [log.alcohol_consumption for log in logs]
    smoking_days = [log.smoking for log in logs]

    features = {
        "age": float(profile.age),
        "bmi": float(profile.bmi),
        "sex": profile.sex,
        "urination_mean": _series_metrics(urination)["mean"],
        "urination_max": _series_metrics(urination)["max"],
        "urination_slope": _series_metrics(urination)["slope"],
        "thirst_frequency_mean": _series_metrics(thirst_frequency)["mean"],
        "thirst_frequency_max": _series_metrics(thirst_frequency)["max"],
        "thirst_frequency_slope": _series_metrics(thirst_frequency)["slope"],
        "thirst_level_mean": _series_metrics(thirst_level)["mean"],
        "thirst_level_max": _series_metrics(thirst_level)["max"],
        "thirst_level_slope": _series_metrics(thirst_level)["slope"],
        "fatigue_level_mean": _series_metrics(fatigue_level)["mean"],
        "fatigue_level_max": _series_metrics(fatigue_level)["max"],
        "fatigue_level_slope": _series_metrics(fatigue_level)["slope"],
        "days_inactive": float(sum(inactive_days)),
        "days_with_alcohol": float(sum(alcohol_days)),
        "days_with_smoking": float(sum(smoking_days)),
        "days_high_thirst": float(sum(level >= 3 for level in thirst_level)),
        "days_high_fatigue": float(sum(level >= 4 for level in fatigue_level)),
    }
    return features


def _get_model_artifact() -> Optional[Dict[str, Any]]:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if MODEL_PATH.exists():
        try:
            _MODEL_CACHE = load_model_artifact(MODEL_PATH)
        except Exception:
            _MODEL_CACHE = None
    return _MODEL_CACHE


def _score_probability(features: Dict[str, float]) -> tuple[float, Dict[str, float]]:
    age_score = min(1.0, max(0.0, (features["age"] - 18.0) / 60.0))
    bmi_score = min(1.0, max(0.0, (features["bmi"] - 18.5) / 15.0))
    urination_score = min(1.0, features["urination_mean"] / 15.0)
    thirst_score = min(1.0, features["thirst_level_mean"] / 4.0)
    thirst_frequency_score = min(1.0, features["thirst_frequency_mean"] / 10.0)
    fatigue_score = min(1.0, features["fatigue_level_mean"] / 5.0)
    inactivity_score = features["days_inactive"] / DAYS_REQUIRED
    alcohol_score = features["days_with_alcohol"] / DAYS_REQUIRED
    smoking_score = features["days_with_smoking"] / DAYS_REQUIRED
    trend_score = max(0.0, features["urination_slope"] / 3.0) + max(0.0, features["thirst_level_slope"] / 2.0) + max(0.0, features["fatigue_level_slope"] / 2.0)

    raw = (
        0.10
        + 0.14 * age_score
        + 0.16 * bmi_score
        + 0.18 * urination_score
        + 0.12 * thirst_score
        + 0.10 * thirst_frequency_score
        + 0.10 * fatigue_score
        + 0.06 * inactivity_score
        + 0.05 * alcohol_score
        + 0.05 * smoking_score
        + 0.04 * trend_score
    )

    synergy = 0.0
    if features["days_high_thirst"] >= 2 and features["urination_mean"] >= 8:
        synergy += 0.05
    if features["days_high_fatigue"] >= 2 and features["days_inactive"] >= 2:
        synergy += 0.04

    probability = float(np.clip(raw + synergy, 0.01, 0.99))
    contributions = {
        "age": age_score,
        "bmi": bmi_score,
        "urination": urination_score,
        "thirst": thirst_score,
        "fatigue": fatigue_score,
        "inactivity": inactivity_score,
        "alcohol": alcohol_score,
        "smoking": smoking_score,
        "trend": min(1.0, trend_score / 3.0),
    }
    return probability, contributions


def _explanations(features: Dict[str, float], contributions: Dict[str, float]) -> List[str]:
    ranked = sorted(contributions.items(), key=lambda item: item[1], reverse=True)
    explanations: List[str] = []
    mapping = {
        "age": f"Age is elevated at {features['age']:.0f}.",
        "bmi": f"BMI is elevated at {features['bmi']:.1f}.",
        "urination": f"Urination frequency averaged {features['urination_mean']:.1f} per day.",
        "thirst": f"Thirst level averaged {features['thirst_level_mean']:.1f} over 3 days.",
        "fatigue": f"Fatigue level averaged {features['fatigue_level_mean']:.1f} over 3 days.",
        "inactivity": f"Physical inactivity was recorded on {int(features['days_inactive'])} of 3 days.",
        "alcohol": f"Alcohol use was recorded on {int(features['days_with_alcohol'])} of 3 days.",
        "smoking": f"Smoking was recorded on {int(features['days_with_smoking'])} of 3 days.",
        "trend": "Symptoms showed a worsening trend across the 3-day window.",
    }
    for key, _score in ranked[:3]:
        explanations.append(mapping[key])
    return explanations


def predict_session(session_id: str) -> Dict[str, Any]:
    with LOCK:
        session = SESSIONS.get(session_id)
        if session is None:
            raise ValueError("Session not found.")
        if session.session_complete:
            return session.prediction  # type: ignore[return-value]

    features = build_session_features(session)
    model_artifact = _get_model_artifact()

    if model_artifact and model_artifact.get("workflow") == "mobile_session_v1":
        model_pipeline = model_artifact["model_pipeline"]
        input_df = pd.DataFrame([{column: features[column] for column in SESSION_FEATURE_COLUMNS}])
        probability = float(model_pipeline.predict_proba(input_df)[:, 1][0])
        risk_level = map_probability_to_risk(probability)
        contributions = {
            "age": min(1.0, features["age"] / 90.0),
            "bmi": min(1.0, features["bmi"] / 45.0),
            "urination": min(1.0, features["urination_mean"] / 15.0),
            "thirst": min(1.0, features["thirst_level_mean"] / 4.0),
            "fatigue": min(1.0, features["fatigue_level_mean"] / 5.0),
            "inactivity": min(1.0, features["days_inactive"] / DAYS_REQUIRED),
            "alcohol": min(1.0, features["days_with_alcohol"] / DAYS_REQUIRED),
            "smoking": min(1.0, features["days_with_smoking"] / DAYS_REQUIRED),
            "trend": min(1.0, max(0.0, features["urination_slope"]) / 3.0),
        }
    else:
        probability, contributions = _score_probability(features)
        risk_level = map_probability_to_risk(probability)
    prediction = {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "risk_level": risk_level,
        "probability": round(probability, 4),
        "model_version": model_artifact.get("workflow", MODEL_VERSION),
        "prediction_time": datetime.now(timezone.utc),
        "explanation": _explanations(features, contributions),
        "features": features,
    }

    with LOCK:
        session.prediction = prediction
        session.status = "completed"
        PREDICTIONS.append(prediction)
        return prediction


def get_latest_prediction(user_id: str) -> Dict[str, Any]:
    with LOCK:
        for prediction in reversed(PREDICTIONS):
            if prediction["user_id"] == user_id:
                return prediction
    raise ValueError("Prediction not found for user.")


def store_training_record(record: Dict[str, Any]) -> Dict[str, Any]:
    with LOCK:
        TRAINING_DATA.append(record)
    return {"status": "success", "record_saved": True}
