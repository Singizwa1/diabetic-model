from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def create_bmi_from_height_weight(df: pd.DataFrame) -> pd.Series:
    """Calculate BMI from Height (Ht) and Weight (Wt).
    
    BMI = Weight (kg) / (Height (m))^2
    Assuming ht is in cm and wt is in kg
    """
    height_m = df['ht'] / 100.0
    bmi = df['wt'] / (height_m ** 2)
    return bmi


def create_temperature_from_activity_health(df: pd.DataFrame) -> pd.Series:
    """Generate synthetic body temperature based on Activity and health factors.
    
    Base temperature: 36.8°C (normal)
    Activity affects temperature:
    - High activity: slight elevation (37.0-37.2)
    - Low activity: baseline or slightly lower
    - Alcohol/Smoking: minor elevation
    """
    base_temp = 36.8
    
    activity_effect = (1 - df['activity'].astype(float)) * 0.2  # Inverse: inactive -> higher temp
    alcohol_effect = df['alcohol'].astype(float) * 0.1
    smoking_effect = df['smoking'].astype(float) * 0.15
    
    temperature = base_temp + activity_effect + alcohol_effect + smoking_effect
    
    # Add small random noise for realism
    noise = np.random.normal(0, 0.1, len(df))
    temperature = temperature + noise
    temperature = np.clip(temperature, 35.5, 39.0)
    
    return temperature


def create_lifestyle_from_activities(df: pd.DataFrame) -> pd.Series:
    """Create categorical lifestyle variable from Activity, Alcohol, and Smoking.
    
    Categories:
    - 'active': Activity=1, no Alcohol, no Smoking
    - 'moderate': Activity=1 or moderate Alcohol/Smoking
    - 'sedentary': Activity=0, Smoking=1 or high Alcohol
    - 'unhealthy': Activity=0, Smoking=1, Alcohol=1
    """
    lifestyle = []
    
    for idx, row in df.iterrows():
        activity = int(row['activity'])
        alcohol = int(row['alcohol'])
        smoking = int(row['smoking'])
        
        if activity == 1 and alcohol == 0 and smoking == 0:
            lifestyle.append('active')
        elif activity == 1 or (alcohol + smoking <= 1):
            lifestyle.append('moderate')
        elif smoking == 1:
            lifestyle.append('sedentary')
        else:
            lifestyle.append('unhealthy')
    
    return pd.Series(lifestyle)


def create_urination_frequency_from_health(df: pd.DataFrame) -> pd.Series:
    """Create synthetic urination frequency based on health risk factors.
    
    Higher risk factors (BMI, age, inactivity) correlate with higher urination frequency.
    Normal range: 3-15 times per day
    """
    bmi = create_bmi_from_height_weight(df)
    age = df['age'].astype(float)
    activity = df['activity'].astype(float)
    
    # Risk-based calculation
    bmi_factor = np.clip((bmi - 18.5) / 10.0, 0, 1)
    age_factor = np.clip((age - 30) / 40.0, 0, 1)
    activity_factor = 1.0 - activity  # Inverse: low activity = high urination risk
    
    base_frequency = 6.0
    risk_contribution = (
        bmi_factor * 2.0 +
        age_factor * 1.5 +
        activity_factor * 2.0
    )
    
    frequency = base_frequency + risk_contribution
    frequency = np.clip(frequency, 3, 15)
    frequency = np.round(frequency).astype(int)
    
    return frequency


def create_diabetes_target_from_health_factors(df: pd.DataFrame) -> pd.Series:
    """Create synthetic diabetes target variable based on health risk factors.
    
    Risk factors:
    - High BMI (> 25): positive indicator
    - Age > 45: positive indicator
    - High income changes: potential stress indicator
    - Low activity: positive indicator
    - Smoking/Alcohol: positive indicators
    
    This is a realistic health risk scoring system.
    """
    bmi = create_bmi_from_height_weight(df)
    age = df['age'].astype(float)
    activity = df['activity'].astype(float)
    smoking = df['smoking'].astype(float)
    alcohol = df['alcohol'].astype(float)
    
    # Calculate risk score (0-1 scale)
    bmi_risk = np.clip((bmi - 18.5) / 25.0, 0, 1)
    age_risk = np.clip((age - 30) / 40.0, 0, 1)
    activity_risk = 1.0 - activity  # Inverse: low activity = high risk
    lifestyle_risk = (smoking + alcohol) / 2.0
    
    risk_score = (
        bmi_risk * 0.35 +
        age_risk * 0.25 +
        activity_risk * 0.25 +
        lifestyle_risk * 0.15
    )
    
    # Add stochasticity for realism (higher risk = higher prob of diabetes=1)
    random_threshold = np.random.uniform(0.3, 0.7, len(df))
    diabetes = (risk_score > random_threshold).astype(int)
    
    return diabetes


def engineer_features(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Transform raw dataset into required model features.
    
    Creates:
    - bmi: from Height and Weight
    - temperature: synthetically generated from activity/health factors
    - urination_frequency: generated from health risk factors
    - lifestyle: categorical from Activity, Alcohol, Smoking
    - diabetes: target variable from health risk factors
    """
    np.random.seed(seed)
    
    engineered = df.copy()
    engineered['bmi'] = create_bmi_from_height_weight(engineered)
    engineered['temperature'] = create_temperature_from_activity_health(engineered)
    engineered['urination_frequency'] = create_urination_frequency_from_health(engineered)
    engineered['lifestyle'] = create_lifestyle_from_activities(engineered)
    engineered['diabetes'] = create_diabetes_target_from_health_factors(engineered)
    
    # Keep only required columns for modeling
    model_columns = ['bmi', 'temperature', 'urination_frequency', 'lifestyle', 'diabetes']
    engineered = engineered[model_columns]
    
    return engineered
