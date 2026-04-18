from __future__ import annotations

import json

from app.model import train_from_excel


if __name__ == "__main__":
    result = train_from_excel("data/Dataset_Diabetes_Final.xlsx", "Sheet1")
    print(json.dumps(result, indent=2, default=str))
