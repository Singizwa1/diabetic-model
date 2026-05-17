#!/usr/bin/env python3
"""
Quick start setup script for Diabetes Risk Prediction API.

Steps:
1. Creates database tables
2. Verifies Redis connection
3. Loads ML model
4. Creates admin user
5. Runs health check
"""

import sys
from pathlib import Path
import logging

from sqlalchemy import text

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings
from app.database import Base, engine, SessionLocal
from app.cache import check_redis_connection
from app.models import User
from app.core.security import hash_password
from app.services.ml_service import MLService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


def setup_database() -> None:
    """Create all database tables."""
    logger.info("📊 Setting up database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as exc:
        logger.error(f"❌ Database setup failed: {str(exc)}")
        sys.exit(1)


def setup_redis() -> None:
    """Verify Redis connection."""
    logger.info("🔴 Checking Redis connection...")
    if check_redis_connection():
        logger.info("✅ Redis connected successfully")
        return

    logger.error("❌ Redis connection failed - token auth will not work")
    logger.error(f"   Expected Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    sys.exit(1)


def load_ml_model() -> None:
    """Load and verify ML model."""
    logger.info("🤖 Loading ML model...")
    try:
        model_service = MLService()
        model_service.load_model()
        logger.info("✅ ML model loaded successfully")
    except Exception as exc:
        logger.warning(f"⚠️ ML model loading failed (fallback will be used): {str(exc)}")


def create_admin_user() -> None:
    """Create default admin user if it doesn't exist."""
    logger.info("👤 Setting up admin user...")

    db = SessionLocal()
    try:
        admin_exists = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if admin_exists:
            logger.info(f"✅ Admin user already exists: {settings.ADMIN_EMAIL}")
            return

        admin_user = User(
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            full_name="System Administrator",
            is_active=True,
            is_admin=True,
        )

        db.add(admin_user)
        db.commit()
        logger.info(f"✅ Admin user created: {settings.ADMIN_EMAIL}")
        logger.info("   Admin password loaded from environment")
        logger.info("   ⚠️ Keep ADMIN_PASSWORD secret and rotate in production")

    except Exception as exc:
        logger.error(f"❌ Admin user creation failed: {str(exc)}")
        db.rollback()
    finally:
        db.close()


def health_check() -> bool:
    """Run basic health check."""
    logger.info("🏥 Running health check...")

    checks = {
        "Database": False,
        "Redis": False,
        "ML Model": False,
    }

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["Database"] = True
    except Exception:
        pass

    checks["Redis"] = check_redis_connection()

    try:
        model_service = MLService()
        model_service.load_model()
        checks["ML Model"] = True
    except Exception:
        pass

    logger.info("Health Check Results:")
    for component, status in checks.items():
        symbol = "✅" if status else "❌"
        logger.info(f"  {symbol} {component}: {'OK' if status else 'FAILED'}")

    return all(checks.values())


def main() -> None:
    """Run all setup steps."""
    logger.info("=" * 60)
    logger.info("🚀 Diabetes Risk Prediction API - Quick Start Setup")
    logger.info("=" * 60)

    logger.info("\n📋 Checking environment variables...")
    required_vars = [
        "DATABASE_URL",
        "REDIS_HOST",
        "SECRET_KEY",
        "ADMIN_EMAIL",
        "ADMIN_PASSWORD",
    ]

    missing_vars = [var for var in required_vars if not getattr(settings, var, None)]
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        logger.error("   Please create .env file with required settings")
        sys.exit(1)

    logger.info("✅ All required environment variables present")

    logger.info("\n" + "=" * 60)
    setup_database()
    setup_redis()
    load_ml_model()
    create_admin_user()

    logger.info("\n" + "=" * 60)
    success = health_check()

    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✅ Setup completed successfully!")
        logger.info("\n📝 Next steps:")
        logger.info("  1. Start the API: python -m uvicorn app.main:app --reload")
        logger.info("  2. View Swagger docs: http://localhost:8000/docs")
        logger.info("\n🔑 Admin credentials:")
        logger.info(f"   Email: {settings.ADMIN_EMAIL}")
        logger.info("   Password: [hidden - use ADMIN_PASSWORD in .env]")
    else:
        logger.error("❌ Setup completed with errors - see above for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
