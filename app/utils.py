from __future__ import annotations

from typing import Optional

import numpy as np

LOW_RISK_THRESHOLD = 0.30
HIGH_RISK_THRESHOLD = 0.70


def map_probability_to_risk(probability: float) -> str:
    """Map probability score into business risk buckets."""
    if probability < LOW_RISK_THRESHOLD:
        return "Low"
    if probability < HIGH_RISK_THRESHOLD:
        return "Medium"
    return "High"


def generate_urination_frequency_from_label(
    diabetes_label: int,
    rng: Optional[np.random.Generator] = None,
) -> int:
    """
    Generate synthetic urination frequency from diabetes label using requested
    medically realistic distributions.
    """
    if rng is None:
        rng = np.random.default_rng()

    if int(diabetes_label) == 1:
        value = rng.normal(loc=10.0, scale=2.0)
    else:
        value = rng.normal(loc=6.0, scale=1.5)

    value = float(np.clip(value, 3, 15))
    return int(round(value))


def generate_urination_frequency_for_inference(
    bmi: float,
    temperature: float,
    lifestyle: str,
    rng: Optional[np.random.Generator] = None,
) -> int:
    """
    Generate urination frequency for live predictions when label is unknown.
    Uses simple deterministic health heuristics with controlled noise.
    """
    if rng is None:
        rng = np.random.default_rng()

    lifestyle_value = (lifestyle or "").strip().lower()
    lifestyle_adjustment = {
        "sedentary": 1.2,
        "inactive": 1.2,
        "moderate": 0.5,
        "active": 0.0,
        "very active": -0.2,
        "smoker": 0.8,
        "alcohol": 0.5,
        "healthy": -0.3,
    }.get(lifestyle_value, 0.3)

    bmi_adjustment = max(0.0, (float(bmi) - 25.0) * 0.12)
    temp_adjustment = max(0.0, (float(temperature) - 36.8) * 1.8)
    noisy_baseline = 6.0 + rng.normal(0.0, 1.0)

    value = noisy_baseline + lifestyle_adjustment + bmi_adjustment + temp_adjustment
    value = float(np.clip(value, 3, 15))
    return int(round(value))
