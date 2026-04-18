from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.model import load_model_artifact
from app.retrain import add_new_labeled_data, retrain_model
from app.schemas import (
    DailyLogRequest,
    DailyLogResponse,
    LatestPredictionResponse,
    PredictionResponse,
    UserProfileRequest,
    ProfileResponse,
    RetrainRequest,
    SessionStatusResponse,
    StartSessionRequest,
    StartSessionResponse,
    TrainingDataRequest,
    TrainingDataResponse,
)
from app.utils import generate_urination_frequency_for_inference, map_probability_to_risk
from app.workflow import (
    MODEL_VERSION,
    DAYS_REQUIRED,
    add_daily_log,
    create_or_update_profile,
    get_latest_prediction,
    get_session,
    predict_session,
    start_session,
    store_training_record,
)

MODEL_PATH = Path("saved_model") / "model.pkl"

app = FastAPI(title="Diabetes Risk Prediction API", version="2.0.0")

model_artifact: Optional[Dict[str, Any]] = None


class PredictRequest(BaseModel):
    bmi: float
    temperature: float
    lifestyle: str
    urination_frequency: Optional[int] = None


class AddDataRequest(BaseModel):
    bmi: float
    temperature: float
    lifestyle: str
    diabetes: int
    urination_frequency: Optional[int] = None


@app.on_event("startup")
def startup_event() -> None:
    global model_artifact
    if MODEL_PATH.exists():
        model_artifact = load_model_artifact(MODEL_PATH)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "model_loaded": model_artifact is not None,
        "model_path": str(MODEL_PATH),
        "api_version": "2.0.0",
        "workflow_version": MODEL_VERSION,
    }


@app.post("/profile", response_model=ProfileResponse)
def profile(payload: UserProfileRequest) -> ProfileResponse:
    profile_obj = create_or_update_profile(
        user_id=payload.user_id,
        age=payload.age,
        bmi=payload.bmi,
        sex=payload.sex,
    )
    return ProfileResponse(
        status="success",
        profile_saved=True,
        user_id=profile_obj.user_id,
        updated_at=profile_obj.updated_at,
    )


@app.post("/sessions", response_model=StartSessionResponse)
def create_session(payload: StartSessionRequest) -> StartSessionResponse:
    try:
        session = start_session(payload.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StartSessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        status=session.status,
        days_required=DAYS_REQUIRED,
        days_received=session.days_received,
        created_at=session.created_at,
    )


@app.post("/sessions/{session_id}/daily-log", response_model=DailyLogResponse)
def submit_daily_log(session_id: str, payload: DailyLogRequest) -> DailyLogResponse:
    try:
        session = add_daily_log(session_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DailyLogResponse(
        status="success",
        session_id=session.session_id,
        day=payload.day,
        days_received=session.days_received,
        days_remaining=session.days_remaining,
        session_complete=session.session_complete,
    )


@app.get("/sessions/{session_id}", response_model=SessionStatusResponse)
def session_status(session_id: str) -> SessionStatusResponse:
    try:
        session = get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SessionStatusResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        status=session.status,
        days_required=DAYS_REQUIRED,
        days_received=session.days_received,
        days_remaining=session.days_remaining,
        session_complete=session.session_complete,
    )


@app.post("/sessions/{session_id}/predict", response_model=PredictionResponse)
def predict_session_risk(session_id: str) -> PredictionResponse:
    try:
        prediction = predict_session(session_id)
    except ValueError as exc:
        message = str(exc)
        raise HTTPException(status_code=400 if "completed daily logs" in message or "not found" not in message else 404, detail=message) from exc

    return PredictionResponse(**prediction)


@app.get("/users/{user_id}/prediction/latest", response_model=LatestPredictionResponse)
def latest_prediction(user_id: str) -> LatestPredictionResponse:
    try:
        prediction = get_latest_prediction(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return LatestPredictionResponse(
        user_id=prediction["user_id"],
        session_id=prediction["session_id"],
        risk_level=prediction["risk_level"],
        probability=prediction["probability"],
        predicted_at=prediction["prediction_time"],
    )


@app.post("/training-data", response_model=TrainingDataResponse)
def training_data(payload: TrainingDataRequest) -> TrainingDataResponse:
    record = payload.model_dump()
    record["received_at"] = pd.Timestamp.utcnow().isoformat()
    try:
        store_training_record(record)
        return TrainingDataResponse(status="success", record_saved=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/add-data")
def add_data(payload: AddDataRequest) -> Dict[str, Any]:
    urination_frequency = (
        payload.urination_frequency
        if payload.urination_frequency is not None
        else generate_urination_frequency_for_inference(
            bmi=payload.bmi,
            temperature=payload.temperature,
            lifestyle=payload.lifestyle,
        )
    )

    record = {
        "bmi": payload.bmi,
        "temperature": payload.temperature,
        "lifestyle": payload.lifestyle,
        "urination_frequency": urination_frequency,
        "diabetes": payload.diabetes,
    }

    try:
        return add_new_labeled_data(record)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/retrain")
def retrain(_: RetrainRequest | None = None) -> Dict[str, Any]:
    global model_artifact

    try:
        result = retrain_model()
        model_artifact = load_model_artifact(MODEL_PATH)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    if model_artifact is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    return {
        "best_model": model_artifact.get("model_name"),
        "selected_metrics": model_artifact.get("selected_metrics", {}),
        "all_model_metrics": model_artifact.get("metrics", []),
        "trained_at_utc": model_artifact.get("trained_at_utc"),
        "training_summary": model_artifact.get("training_summary", {}),
        "api_version": "2.0.0",
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictRequest) -> PredictionResponse:
    """
    Compatibility endpoint for the older single-shot workflow.
    Internally maps to the new risk bucket logic.
    """
    urination_frequency = (
        payload.urination_frequency
        if payload.urination_frequency is not None
        else generate_urination_frequency_for_inference(
            bmi=payload.bmi,
            temperature=payload.temperature,
            lifestyle=payload.lifestyle,
        )
    )
    session_like_probability = 0.05
    session_like_probability += min(0.25, max(0.0, (payload.bmi - 18.5) / 20.0) * 0.25)
    session_like_probability += min(0.20, max(0.0, (payload.temperature - 36.8) * 0.1))
    session_like_probability += min(0.25, urination_frequency / 40.0)
    session_like_probability += 0.1 if payload.lifestyle.lower() in {"sedentary", "unhealthy"} else 0.0
    probability = float(max(0.01, min(0.99, session_like_probability)))

    return PredictionResponse(
        session_id="compat",
        user_id="compat",
        risk_level=map_probability_to_risk(probability),
        probability=round(probability, 4),
        model_version="compat_v1",
        prediction_time=pd.Timestamp.utcnow().to_pydatetime(),
        explanation=["Compatibility prediction for the legacy endpoint."],
    )
