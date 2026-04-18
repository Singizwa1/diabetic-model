from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from app.model import save_model_artifact, train_from_excel
from app.mobile_training import MODEL_PATH
from app.preprocessing import standardize_column_names

BASE_DATASET_PATH = Path("data") / "Dataset_Diabetes_Final.xlsx"
NEW_DATA_PATH = Path("data") / "new_data.csv"


def _resolve_base_dataset_path(base_excel_path: Path) -> Path:
    if base_excel_path.exists():
        return base_excel_path

    data_dir = base_excel_path.parent
    for candidate in sorted(data_dir.glob("*.xlsx")):
        if not candidate.name.startswith("~$"):
            return candidate

    raise FileNotFoundError(
        f"Base dataset not found at {base_excel_path}. Place your Excel file there first."
    )


def add_new_labeled_data(record: Dict[str, Any], csv_path: Path = NEW_DATA_PATH) -> Dict[str, Any]:
    """Append a labeled observation for future retraining."""
    payload = standardize_column_names(pd.DataFrame([record]))
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    header = not csv_path.exists()
    payload.to_csv(csv_path, mode="a", header=header, index=False)

    return {
        "status": "success",
        "stored_rows": int(payload.shape[0]),
        "csv_path": str(csv_path),
    }


def retrain_model(
    base_excel_path: Path = BASE_DATASET_PATH,
    new_data_path: Path = NEW_DATA_PATH,
    sheet_name: str = "Sheet1",
) -> Dict[str, Any]:
    """Retrain the mobile session model using the base Excel data."""
    resolved_base_excel_path = _resolve_base_dataset_path(base_excel_path)

    result = train_from_excel(excel_path=str(resolved_base_excel_path), sheet_name=sheet_name)
    return {
        "status": "success",
        "best_model": result["model_name"],
        "metrics": result["metrics"],
        "comparison_table": result["comparison_table"],
        "training_summary": result["training_summary"],
        "rows_used_for_training": int(result["training_summary"].get("session_shape", (0, 0))[0]),
        "saved_model_path": str(MODEL_PATH),
        "base_dataset_path": str(resolved_base_excel_path),
    }
