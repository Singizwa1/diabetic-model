"""
Routes module for Diabetes Risk Prediction System API.

Contains API endpoint definitions for:
- Authentication (register, login)
- User profiles (CRUD)
- Assessment sessions (create, manage daily logs)
- Predictions (run inference)
- Admin operations
- Notifications and health checks
"""

from app.routes import auth_routes, profile_routes, session_routes, prediction_routes, admin_routes, health_routes

__all__ = [
    "auth_routes",
    "profile_routes", 
    "session_routes",
    "prediction_routes",
    "admin_routes",
    "health_routes"
]
