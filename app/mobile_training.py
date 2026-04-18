from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from xgboost import XGBClassifier
except Exception as exc:  # pragma: no cover
    XGBClassifier = None
    XGBOOST_IMPORT_ERROR = exc
else:
    XGBOOST_IMPORT_ERROR = None

MODEL_DIR = Path("saved_model")
MODEL_PATH = MODEL_DIR / "model.pkl"
RANDOM_STATE = 42
DAYS_REQUIRED = 3
SESSION_FEATURE_COLUMNS = [
    "age",
    "bmi",
    "sex",
    "urination_mean",
    "urination_max",
    "urination_slope",
    "thirst_frequency_mean",
    "thirst_frequency_max",
    "thirst_frequency_slope",
    "thirst_level_mean",
    "thirst_level_max",
    "thirst_level_slope",
    "fatigue_level_mean",
    "fatigue_level_max",
    "fatigue_level_slope",
    "days_inactive",
    "days_with_alcohol",
    "days_with_smoking",
    "days_high_thirst",
    "days_high_fatigue",
]
NUMERIC_FEATURES = [c for c in SESSION_FEATURE_COLUMNS if c != "sex"]
CATEGORICAL_FEATURES = ["sex"]


@dataclass(frozen=True)
class SessionSnapshot:
    age: float
    bmi: float
    sex: str
    urination: List[float]
    thirst_frequency: List[float]
    thirst_level: List[float]
    fatigue_level: List[float]
    inactive_days: List[bool]
    alcohol_days: List[bool]
    smoking_days: List[bool]


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={column: column.strip().lower().replace(" ", "_") for column in df.columns})


def load_dataset_from_excel(excel_path: str, sheet_name: str = "Sheet1") -> pd.DataFrame:
    return _standardize_columns(pd.read_excel(excel_path, sheet_name=sheet_name))


def _ensure_sex_value(value: Any) -> str:
    if pd.isna(value):
        return "other"
    text = str(value).strip().lower()
    mapping = {
        "1": "male",
        "2": "female",
        "m": "male",
        "male": "male",
        "f": "female",
        "female": "female",
    }
    return mapping.get(text, "other")


def _height_to_bmi(row: pd.Series) -> float:
    if "bmi" in row and not pd.isna(row.get("bmi")):
        return float(row["bmi"])
    height = row.get("height", row.get("ht"))
    weight = row.get("weight", row.get("wt"))
    if pd.isna(height) or pd.isna(weight):
        raise ValueError("Dataset must contain either bmi or both ht/wt columns.")
    height_value = float(height)
    height_m = height_value if height_value <= 3.0 else height_value / 100.0
    return float(weight) / (height_m * height_m)


def _base_risk(age: float, bmi: float, activity: float, alcohol: float, smoking: float) -> float:
    age_score = np.clip((age - 25.0) / 55.0, 0.0, 1.0)
    bmi_score = np.clip((bmi - 18.5) / 15.0, 0.0, 1.0)
    inactivity_score = 1.0 - activity
    lifestyle_score = 0.5 * alcohol + 0.5 * smoking
    return float(0.25 * age_score + 0.30 * bmi_score + 0.20 * inactivity_score + 0.25 * lifestyle_score)


def _simulate_session(row: pd.Series, rng: np.random.Generator) -> Dict[str, Any]:
    age = float(row.get("age", 45.0))
    bmi = _height_to_bmi(row)
    sex = _ensure_sex_value(row.get("sex", row.get("gender", "other")))
    activity = float(row.get("activity", 0.0))
    alcohol = float(row.get("alcohol", 0.0))
    smoking = float(row.get("smoking", 0.0))
    baseline_thirst_frequency = float(row.get("thirst_frequency", row.get("thirst_frequency", 2.0)))
    baseline_fatigue = float(row.get("fatigue_level", 2.0))
    risk = _base_risk(age, bmi, activity, alcohol, smoking)

    day_offsets = np.array([0.0, 0.35, 0.7])
    urination = []
    thirst_frequency = []
    thirst_level = []
    fatigue_level = []
    inactive_days = []
    alcohol_days = []
    smoking_days = []

    for offset in day_offsets:
        daily_trend = risk + offset
        urination.append(float(np.clip(np.round(5.0 + daily_trend * 6.0 + rng.normal(0.0, 0.8)), 3, 15)))
        thirst_frequency.append(float(np.clip(np.round(baseline_thirst_frequency + daily_trend * 2.0 + rng.normal(0.0, 0.8)), 0, 15)))
        thirst_level.append(float(np.clip(np.round(1.0 + daily_trend * 3.0 + rng.normal(0.0, 0.4)), 1, 4)))
        fatigue_level.append(float(np.clip(np.round(baseline_fatigue + daily_trend * 1.2 + rng.normal(0.0, 0.5)), 1, 5)))
        inactive_days.append(bool(activity < 0.5 or rng.random() < risk * 0.4))
        alcohol_days.append(bool(alcohol > 0.5 or rng.random() < risk * 0.25))
        smoking_days.append(bool(smoking > 0.5 or rng.random() < risk * 0.25))

    return {
        "age": age,
        "bmi": bmi,
        "sex": sex,
        "urination_mean": float(np.mean(urination)),
        "urination_max": float(np.max(urination)),
        "urination_slope": float(np.polyfit(np.arange(3), urination, 1)[0]),
        "thirst_frequency_mean": float(np.mean(thirst_frequency)),
        "thirst_frequency_max": float(np.max(thirst_frequency)),
        "thirst_frequency_slope": float(np.polyfit(np.arange(3), thirst_frequency, 1)[0]),
        "thirst_level_mean": float(np.mean(thirst_level)),
        "thirst_level_max": float(np.max(thirst_level)),
        "thirst_level_slope": float(np.polyfit(np.arange(3), thirst_level, 1)[0]),
        "fatigue_level_mean": float(np.mean(fatigue_level)),
        "fatigue_level_max": float(np.max(fatigue_level)),
        "fatigue_level_slope": float(np.polyfit(np.arange(3), fatigue_level, 1)[0]),
        "days_inactive": float(sum(inactive_days)),
        "days_with_alcohol": float(sum(alcohol_days)),
        "days_with_smoking": float(sum(smoking_days)),
        "days_high_thirst": float(sum(level >= 3 for level in thirst_level)),
        "days_high_fatigue": float(sum(level >= 4 for level in fatigue_level)),
        "risk": risk,
    }


def _generate_target(features: pd.DataFrame, rng: np.random.Generator) -> pd.Series:
    probability = (
        0.05
        + 0.10 * np.clip((features["age"] - 35.0) / 50.0, 0.0, 1.0)
        + 0.15 * np.clip((features["bmi"] - 20.0) / 15.0, 0.0, 1.0)
        + 0.10 * np.clip(features["urination_mean"] / 15.0, 0.0, 1.0)
        + 0.12 * np.clip(features["thirst_level_mean"] / 4.0, 0.0, 1.0)
        + 0.10 * np.clip(features["fatigue_level_mean"] / 5.0, 0.0, 1.0)
        + 0.08 * np.clip(features["days_inactive"] / DAYS_REQUIRED, 0.0, 1.0)
        + 0.05 * np.clip(features["days_with_alcohol"] / DAYS_REQUIRED, 0.0, 1.0)
        + 0.05 * np.clip(features["days_with_smoking"] / DAYS_REQUIRED, 0.0, 1.0)
        + 0.07 * np.clip(features["days_high_thirst"] / DAYS_REQUIRED, 0.0, 1.0)
        + 0.08 * np.clip(features["days_high_fatigue"] / DAYS_REQUIRED, 0.0, 1.0)
        + 0.10 * np.clip(np.maximum(features["urination_slope"], 0.0) / 2.5, 0.0, 1.0)
        + 0.10 * np.clip(np.maximum(features["thirst_level_slope"], 0.0) / 1.5, 0.0, 1.0)
    )
    probability = np.clip(probability, 0.02, 0.98)
    noise = rng.random(len(features))
    return (noise < probability).astype(int)


def build_session_training_frame(raw_df: pd.DataFrame, seed: int = RANDOM_STATE) -> pd.DataFrame:
    raw_df = _standardize_columns(raw_df).drop_duplicates().reset_index(drop=True)
    rng = np.random.default_rng(seed)
    session_rows = [_simulate_session(row, rng) for _, row in raw_df.iterrows()]
    frame = pd.DataFrame(session_rows)
    frame["diabetes"] = _generate_target(frame, rng)
    return frame


def _build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="mean")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def _build_model_candidates() -> Dict[str, Any]:
    if XGBClassifier is None:
        raise ImportError("xgboost is required but is not available.") from XGBOOST_IMPORT_ERROR
    return {
        "logistic_regression": LogisticRegression(max_iter=2000, random_state=RANDOM_STATE),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            random_state=RANDOM_STATE,
            class_weight="balanced",
        ),
        "xgboost": XGBClassifier(
            n_estimators=250,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=RANDOM_STATE,
        ),
    }


def _evaluate_model(y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
    }


def train_mobile_model_from_excel(excel_path: str, sheet_name: str = "Sheet1") -> Tuple[Dict[str, Any], pd.DataFrame, Dict[str, Any]]:
    raw_df = load_dataset_from_excel(excel_path, sheet_name=sheet_name)
    if raw_df.empty:
        raise ValueError("Dataset is empty.")

    training_df = build_session_training_frame(raw_df)
    summary = {
        "raw_shape": tuple(raw_df.shape),
        "session_shape": tuple(training_df.shape),
        "feature_columns": SESSION_FEATURE_COLUMNS,
    }

    X = training_df[SESSION_FEATURE_COLUMNS].copy()
    y = training_df["diabetes"].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    preprocessor = _build_preprocessor()
    models = _build_model_candidates()

    comparison_rows: List[Dict[str, Any]] = []
    trained_pipelines: Dict[str, Pipeline] = {}

    for model_name, estimator in models.items():
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", estimator),
        ])
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, 1]
        metrics = _evaluate_model(y_test, y_pred, y_proba)
        comparison_rows.append({"model": model_name, **metrics})
        trained_pipelines[model_name] = pipeline

    comparison_df = pd.DataFrame(comparison_rows).sort_values(by="f1_score", ascending=False).reset_index(drop=True)
    best_model_name = str(comparison_df.iloc[0]["model"])
    best_pipeline = trained_pipelines[best_model_name]

    artifact = {
        "workflow": "mobile_session_v1",
        "model_name": best_model_name,
        "model_pipeline": best_pipeline,
        "metrics": comparison_df.to_dict(orient="records"),
        "selected_metrics": comparison_df.iloc[0].to_dict(),
        "trained_at_utc": pd.Timestamp.utcnow().isoformat(),
        "training_summary": summary,
        "feature_columns": SESSION_FEATURE_COLUMNS,
    }

    return artifact, comparison_df, summary


def save_model_artifact(artifact: Dict[str, Any], model_path: Path = MODEL_PATH) -> Path:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_path)
    return model_path


def load_model_artifact(model_path: Path = MODEL_PATH) -> Dict[str, Any]:
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_path}.")
    return joblib.load(model_path)
