from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple
import argparse

import pandas as pd

from app.mobile_training import (
    MODEL_PATH,
    load_model_artifact,
    save_model_artifact,
    train_mobile_model_from_excel,
)


def train_and_select_best_model(df: pd.DataFrame) -> Tuple[Dict[str, Any], pd.DataFrame, Dict[str, Any]]:
    raise NotImplementedError("Use train_from_excel for the mobile session workflow.")


def train_from_excel(excel_path: str, sheet_name: str = "Sheet1") -> Dict[str, Any]:
    """Train the mobile 3-day session model from the Excel dataset."""
    artifact, comparison_df, summary = train_mobile_model_from_excel(excel_path=excel_path, sheet_name=sheet_name)
    save_model_artifact(artifact)

    return {
        "model_name": artifact["model_name"],
        "metrics": artifact["metrics"],
        "comparison_table": comparison_df.to_dict(orient="records"),
        "training_summary": summary,
        "saved_model_path": str(MODEL_PATH),
    }


def main() -> None:
    """CLI entrypoint for one-shot model training."""
    parser = argparse.ArgumentParser(description="Train diabetes risk model from Excel dataset")
    parser.add_argument(
        "--excel-path",
        default="data/Dataset_Diabetes_Final.xlsx",
        help="Path to the Excel file that contains the dataset sheet",
    )
    parser.add_argument(
        "--sheet-name",
        default="Sheet1",
        help="Worksheet name for training data",
    )
    args = parser.parse_args()

    result = train_from_excel(excel_path=args.excel_path, sheet_name=args.sheet_name)

    print("Dataset Summary:")
    print(result["training_summary"])
    print("\nModel Comparison:")
    print(pd.DataFrame(result["comparison_table"]).to_string(index=False))
    print("\nSelected Model:", result["model_name"])
    print("Saved Artifact:", result["saved_model_path"])


if __name__ == "__main__":
    main()
