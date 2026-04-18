from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.utils import generate_urination_frequency_from_label

NUMERIC_FEATURES = ["bmi", "temperature", "urination_frequency"]
CATEGORICAL_FEATURES = ["lifestyle"]
REQUIRED_BASE_COLUMNS = ["bmi", "temperature", "urination_frequency", "lifestyle", "diabetes"]
TARGET_COLUMN = "diabetes"


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Convert all column names to lowercase snake-style names."""
    renamed = {
        c: c.strip().lower().replace(" ", "_")
        for c in df.columns
    }
    return df.rename(columns=renamed)


def load_dataset_from_excel(excel_path: str, sheet_name: str = "dataset") -> pd.DataFrame:
    """Load the dataset sheet from Excel and normalize column names."""
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    return standardize_column_names(df)


def summarize_dataframe(df: pd.DataFrame) -> Dict[str, object]:
    """Provide an inspection summary for logging and diagnostics."""
    return {
        "shape": tuple(df.shape),
        "columns": list(df.columns),
        "missing_by_column": df.isna().sum().to_dict(),
        "numeric_summary": df.describe(include="number").to_dict() if not df.empty else {},
    }


def _fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Apply mean imputation for numeric and mode for categorical columns."""
    cleaned = df.copy()

    numeric_columns = cleaned.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = [c for c in cleaned.columns if c not in numeric_columns]

    for col in numeric_columns:
        cleaned[col] = cleaned[col].fillna(cleaned[col].mean())

    for col in categorical_columns:
        mode = cleaned[col].mode(dropna=True)
        if mode.empty:
            cleaned[col] = cleaned[col].fillna("unknown")
        else:
            cleaned[col] = cleaned[col].fillna(mode.iloc[0])

    return cleaned


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean dataset according to project rules:
    - standardize columns
    - remove duplicates
    - fill missing values
    - validate target values
    """
    cleaned = standardize_column_names(df).copy()
    cleaned = cleaned.drop_duplicates().reset_index(drop=True)

    missing_columns = [c for c in REQUIRED_BASE_COLUMNS if c not in cleaned.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    cleaned = _fill_missing_values(cleaned)

    cleaned[TARGET_COLUMN] = cleaned[TARGET_COLUMN].astype(int)
    invalid = ~cleaned[TARGET_COLUMN].isin([0, 1])
    if invalid.any():
        raise ValueError("Target column diabetes must contain only 0/1 values.")

    return cleaned


def build_preprocessor(
    numeric_features: List[str] = NUMERIC_FEATURES,
    categorical_features: List[str] = CATEGORICAL_FEATURES,
) -> ColumnTransformer:
    """Build a preprocessing transformer with imputing, scaling and encoding."""
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
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ]
    )


def split_features_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Split dataframe into model features and target."""
    expected_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    missing_features = [f for f in expected_features if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing model features: {missing_features}")

    X = df[expected_features].copy()
    y = df[TARGET_COLUMN].copy()
    return X, y
