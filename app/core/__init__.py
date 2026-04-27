"""
Core module for Diabetes Risk Prediction System.

Contains:
- Configuration management
- Security helpers
"""

from app.core.config import get_settings, Settings

__all__ = [
    "get_settings",
    "Settings",
]
