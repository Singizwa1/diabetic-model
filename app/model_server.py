from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

ARTIFACT_PATH = Path("saved_model/model.pkl")


class Features(BaseModel):
    age: float
    sex: int
    bmi: float
    urination_frequency_mean: float
    urination_frequency_max: float
    thirst_frequency_mean: float
    thirst_frequency_max: float
    thirst_level_mean: float
    thirst_level_max: float
    fatigue_level_mean: float
    fatigue_level_max: float
    physical_activity_count: float
    alcohol_consumption_count: float
    smoking: int
    days_logged: int


def _load_artifact(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Model artifact not found at {path}")
    art = joblib.load(path)
    # artifact from training is a dict with 'model_pipeline' and 'model_name'
    if isinstance(art, dict) and "model_pipeline" in art:
        return art
    # fallback: assume the loaded object is the pipeline itself
    return {"model_pipeline": art, "model_name": getattr(art, "__class__", type(art)).__name__}


app = FastAPI(title="Diabetes Model Server")


@app.on_event("startup")
def startup_load_model():
    try:
        app.state.artifact = _load_artifact(ARTIFACT_PATH)
        app.state.pipeline = app.state.artifact["model_pipeline"]
        app.state.model_name = app.state.artifact.get("model_name", "unknown")
    except Exception as e:
        # keep server up but mark pipeline as unavailable
        app.state.artifact = None
        app.state.pipeline = None
        app.state.model_name = "not_loaded"
        app.state.load_error = str(e)


@app.get("/health")
def health():
    return {"status": "ok", "model": app.state.model_name}


@app.post("/predict")
def predict(features: Features):
    if app.state.pipeline is None:
        raise HTTPException(status_code=503, detail={"error": "model not loaded", "reason": getattr(app.state, 'load_error', None)})

    # Prepare vector in the same order as MLService._prepare_feature_vector
    feature_order = [
        "age", "sex", "bmi",
        "urination_frequency_mean", "urination_frequency_max",
        "thirst_frequency_mean", "thirst_frequency_max",
        "thirst_level_mean", "thirst_level_max",
        "fatigue_level_mean", "fatigue_level_max",
        "physical_activity_count", "alcohol_consumption_count", "smoking",
        "days_logged",
    ]

    data = {k: getattr(features, k) for k in feature_order}
    vector = np.array([data.get(k, 0) for k in feature_order]).reshape(1, -1)

    try:
        proba = float(app.state.pipeline.predict_proba(vector)[0][1])
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "prediction_failed", "reason": str(e)})

    return {"model": app.state.model_name, "probability": proba, "features": data}
