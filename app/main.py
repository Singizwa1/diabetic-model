"""
FastAPI application factory and startup/shutdown logic.

Features:
- Redis connection management
- Database initialization
- Route registration (31+ endpoints)
- CORS middleware
- Exception handlers
- Health checks with dependency injection
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.core.config import get_settings
from app.database import Base, engine
from app.cache import redis_client, check_redis_connection

# Import all route modules
from app.routes import auth_routes, profile_routes, session_routes, prediction_routes, admin_routes, health_routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


# ==================== STARTUP / SHUTDOWN ====================

async def startup_event():
    """Initialize database and Redis on startup."""
    logger.info("🚀 Starting Diabetes Risk Prediction API...")
    
    # Check Redis
    if check_redis_connection():
        logger.info("✅ Redis connected")
    else:
        logger.warning("⚠️ Redis not available - token auth will fail")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise
    
    # Log configuration
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"📦 API Version: {settings.APP_VERSION}")


async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("🛑 Shutting down API...")
    try:
        redis_client.close()
        logger.info("✅ Redis connection closed")
    except Exception as e:
        logger.warning(f"⚠️ Error closing Redis: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI 0.115+."""
    # Startup
    await startup_event()
    yield
    # Shutdown
    await shutdown_event()


# ==================== EXCEPTION HANDLERS ====================

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# ==================== APP FACTORY ====================

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="ML-powered diabetes risk prediction system with Redis token auth",
        lifespan=lifespan,
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Production: restrict to specific domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # Register route modules (31+ endpoints total)
    # POST /auth/register, /auth/login, /auth/logout + GET /auth/me (4 endpoints)
    app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
    
    # Profile endpoints (4 endpoints)
    app.include_router(profile_routes.router, prefix="/profiles", tags=["Profiles"])
    
    # Session endpoints (6 endpoints)
    app.include_router(session_routes.router, prefix="/sessions", tags=["Assessment Sessions"])
    
    # Prediction endpoints (3 endpoints)
    app.include_router(prediction_routes.router, prefix="/predictions", tags=["Predictions"])
    
    # Admin endpoints (4 endpoints)
    app.include_router(admin_routes.router, prefix="/admin", tags=["Admin"])
    
    # Health endpoints (2 endpoints)
    app.include_router(health_routes.router, prefix="", tags=["Health"])
    
    logger.info(f"✅ Registered all route modules (31+ endpoints total)")
    
    return app


# ==================== ENTRY POINT ====================

app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
    )
