# Diabetes Risk Prediction System - Production Backend Setup Guide

## Overview

This is a production-ready FastAPI backend for the Diabetes Risk Prediction System featuring:
- PostgreSQL database with SQLAlchemy ORM
- JWT authentication & role-based authorization
- Complete REST API with comprehensive endpoints
- Email notifications for high-risk alerts
- Alembic database migrations
- ML model integration with scikit-learn/xgboost

---

## Prerequisites

### Required Software
1. **Python** 3.9+
2. **PostgreSQL** 15+ (running locally or on a server)
3. **Git** (for version control)

### Optional
- **pgAdmin** (GUI for PostgreSQL management)
- **Postman** or **Thunder Client** (API testing)

---

## Step 1: Setup PostgreSQL Database

### Option A: Using Local PostgreSQL (Windows)

1. **Install PostgreSQL** (if not already installed)
   - Download from https://www.postgresql.org/download/windows/
   - During installation, set password for `postgres` user (e.g., `postgres`)
   - Note the port (default: 5432)

2. **Create a new database**
   ```powershell
   psql -U postgres -h localhost
   ```
   
   In the psql prompt:
   ```sql
   CREATE DATABASE diabetes_db;
   CREATE USER diabetes_user WITH PASSWORD 'secure_password_here';
   ALTER ROLE diabetes_user SET client_encoding TO 'utf8';
   ALTER ROLE diabetes_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE diabetes_user SET default_transaction_deferrable TO on;
   ALTER ROLE diabetes_user SET default_transaction_read_only TO off;
   GRANT ALL PRIVILEGES ON DATABASE diabetes_db TO diabetes_user;
   \q
   ```

3. **Verify Connection**
   ```powershell
   psql -U diabetes_user -d diabetes_db -h localhost
   ```

### Option B: Using Docker (Recommended for Production)

```powershell
docker run --name postgres_diabetes `
  -e POSTGRES_USER=diabetes_user `
  -e POSTGRES_PASSWORD=secure_password_here `
  -e POSTGRES_DB=diabetes_db `
  -p 5432:5432 `
  -d postgres:15-alpine
```

---

## Step 2: Setup Python Environment

### 1. Create Virtual Environment
```powershell
python -m venv .venv
```

### 2. Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Upgrade pip
```powershell
python -m pip install --upgrade pip
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## Step 3: Configure Environment Variables

### 1. Copy Environment Template
```powershell
Copy-Item .env.example .env
```

### 2. Edit `.env` File

Update with your actual values:

```env
# Database Configuration
DATABASE_URL=postgresql://diabetes_user:secure_password_here@localhost:5432/diabetes_db

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars-abc123xyz
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# SMTP Configuration (for email notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-specific-password  # Use Gmail App Password

# Admin Configuration
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change-this-in-production

# Application Configuration
APP_NAME=Diabetes Risk Prediction API
APP_VERSION=2.0.0
ENVIRONMENT=development
```

### Important Security Notes:
- **SECRET_KEY**: Generate a secure key:
  ```powershell
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- **Gmail Setup**: Follow this guide for App Password: https://support.google.com/accounts/answer/185833
- In production, use environment variables instead of `.env` file

---

## Step 4: Initialize Alembic Migrations

### 1. Initialize Alembic (if not done yet)
```powershell
alembic init alembic
```

### 2. Update `alembic/env.py`

Replace the sqlalchemy connection block with:

```python
from app.core.config import get_settings
from app.database import Base

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata
```

### 3. Create Initial Migration
```powershell
alembic revision --autogenerate -m "initial_schema"
```

### 4. Apply Migration to Database
```powershell
alembic upgrade head
```

### Verify Tables Created
```powershell
psql -U diabetes_user -d diabetes_db -h localhost

# In psql:
\dt
# Should show: users, user_profiles, assessment_sessions, daily_logs, predictions, etc.
\q
```

---

## Step 5: Initialize Admin User (Optional)

Create a script `scripts/create_admin.py`:

```python
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User
from app.core.security import hash_password
from app.core.config import get_settings

settings = get_settings()

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Check if admin exists
admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()

if not admin:
    admin_user = User(
        email=settings.ADMIN_EMAIL,
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        full_name="System Administrator",
        is_active=True,
        is_admin=True
    )
    db.add(admin_user)
    db.commit()
    print(f"✅ Admin user created: {settings.ADMIN_EMAIL}")
else:
    print(f"⚠️  Admin user already exists: {settings.ADMIN_EMAIL}")

db.close()
```

Run it:
```powershell
python scripts/create_admin.py
```

---

## Step 6: Start the Backend Server

### Development Mode (with auto-reload)
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Expected Output
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

## Step 7: Test the API

### 1. Check Health Endpoint
```powershell
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "api_version": "2.0.0",
  "model_loaded": true,
  "database_connected": true,
  "timestamp": "2024-01-15T12:34:56.789Z"
}
```

### 2. Interactive API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Register a User
```powershell
$body = @{
    email = "user@example.com"
    password = "SecurePass123!"
    full_name = "John Doe"
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:8000/auth/register `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

---

## API Endpoints Overview

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Profiles
- `POST /profiles` - Create health profile
- `GET /profiles` - Get all user profiles
- `GET /profiles/latest` - Get latest profile
- `PUT /profiles/{profile_id}` - Update profile

### Sessions
- `POST /sessions` - Start new assessment session
- `GET /sessions` - Get all user sessions
- `GET /sessions/{session_id}` - Get session details
- `POST /sessions/{session_id}/daily-logs` - Add daily log
- `POST /sessions/{session_id}/complete` - Mark session complete
- `POST /sessions/{session_id}/cancel` - Cancel session

### Predictions
- `POST /predictions/sessions/{session_id}/predict` - Run prediction
- `GET /predictions/latest` - Get latest prediction
- `GET /predictions` - Get all predictions

### Notifications
- `GET /notifications` - Get notifications
- `POST /notifications/{id}/read` - Mark notification as read

### Admin (requires admin role)
- `GET /admin/users` - Get all users
- `GET /admin/users/{user_id}/toggle-admin` - Toggle admin status
- `GET /admin/models` - Get model registry
- `GET /admin/statistics` - System statistics

### Health
- `GET /health` - Health check
- `GET /` - API root info

---

## Database Schema

### Tables Created

```
users
├─ id (UUID, PK)
├─ email (String, Unique)
├─ password_hash (String)
├─ full_name (String, Optional)
├─ is_active (Boolean)
├─ is_admin (Boolean)
├─ created_at (DateTime)
└─ updated_at (DateTime)

user_profiles
├─ id (UUID, PK)
├─ user_id (UUID, FK → users)
├─ age (Integer)
├─ sex (String: "male"/"female")
├─ height_cm (Float)
├─ weight_kg (Float)
├─ bmi (Float)
├─ created_at (DateTime)
└─ updated_at (DateTime)

assessment_sessions
├─ id (UUID, PK)
├─ user_id (UUID, FK → users)
├─ profile_id (UUID, FK → user_profiles)
├─ status (Enum: collecting/completed/predicted/cancelled)
├─ target_days (Integer, default: 3)
├─ started_at (DateTime)
├─ completed_at (DateTime, Optional)
├─ created_at (DateTime)
└─ updated_at (DateTime)

daily_logs
├─ id (UUID, PK)
├─ session_id (UUID, FK → assessment_sessions)
├─ day_number (Integer)
├─ log_date (DateTime)
├─ urination_frequency (Integer)
├─ thirst_frequency (Integer)
├─ thirst_level (Integer: 1-4)
├─ fatigue_level (Integer: 1-5)
├─ physical_activity (Boolean)
├─ alcohol_consumption (Boolean)
├─ smoking (Boolean)
├─ created_at (DateTime)
└─ updated_at (DateTime)

predictions
├─ id (UUID, PK)
├─ session_id (UUID, FK → assessment_sessions, Unique)
├─ user_id (UUID, FK → users)
├─ model_version (String)
├─ probability (Float: 0.0-1.0)
├─ risk_level (Enum: low/medium/high)
├─ feature_payload (JSON, Optional)
└─ created_at (DateTime)

model_registry
├─ id (UUID, PK)
├─ model_version (String, Unique)
├─ workflow_version (String)
├─ artifact_path (String)
├─ metrics (JSON, Optional)
├─ is_active (Boolean)
├─ created_at (DateTime)
└─ updated_at (DateTime)

notifications
├─ id (UUID, PK)
├─ user_id (UUID, FK → users)
├─ title (String)
├─ message (Text)
├─ notification_type (String)
├─ is_read (Boolean)
└─ created_at (DateTime)
```

---

## Deployment Checklist

### Before Going to Production
- [ ] Change SECRET_KEY to a secure random value
- [ ] Update DATABASE_URL to production database
- [ ] Configure SMTP credentials for production email service
- [ ] Set ENVIRONMENT=production
- [ ] Enable HTTPS/SSL on server
- [ ] Restrict CORS origins (remove `"*"`)
- [ ] Use database backups
- [ ] Setup monitoring and logging
- [ ] Configure rate limiting
- [ ] Setup error tracking (Sentry, etc.)
- [ ] Run security audit on dependencies

### Docker Deployment Example

`Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`docker-compose.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: diabetes_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: diabetes_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: .
    environment:
      DATABASE_URL: postgresql://diabetes_user:${DB_PASSWORD}@postgres:5432/diabetes_db
    ports:
      - "8000:8000"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

---

## Troubleshooting

### Issue: "Connection refused" to PostgreSQL
- Ensure PostgreSQL service is running
- Check DATABASE_URL in `.env` is correct
- Verify database exists: `psql -U diabetes_user -l`

### Issue: "ModuleNotFoundError: No module named 'psycopg2'"
```powershell
pip install psycopg2-binary
```

### Issue: Alembic migration fails
```powershell
# Reset migrations (development only!)
alembic downgrade base
alembic upgrade head
```

### Issue: "TypeError: __init__() missing 1 required positional argument: 'drivername'"
Update SQLAlchemy URL format in .env to:
```
postgresql://user:password@host:port/database
```

---

## Performance Optimization

### Database Indexes
Automatically created on:
- `users.email` (unique)
- `users.is_active`
- `assessment_sessions.user_id`
- `assessment_sessions.status`
- `predictions.created_at`
- `predictions.user_id`

### Connection Pooling
Already configured in `app/database.py`:
```python
pool_size=10
max_overflow=20
pool_pre_ping=True  # Verify connections before use
```

### Caching
For high-traffic deployments, consider:
- Redis for session caching
- CDN for static assets
- Database query result caching

---

## Security Best Practices

1. **JWT Token Security**
   - Use strong SECRET_KEY (min 32 chars)
   - Short expiration times (30 min default)
   - Refresh token rotation

2. **Password Security**
   - Bcrypt hashing with salt
   - Password minimum 8 characters
   - Rate limiting on login attempts

3. **API Security**
   - HTTPS/TLS in production
   - CORS restrictions
   - Input validation with Pydantic
   - SQL injection prevention via ORM

4. **Database Security**
   - Strong credentials for database user
   - Principle of least privilege
   - Regular backups
   - Encryption at rest (optional)

---

## Support & Documentation

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Alembic Docs**: https://alembic.sqlalchemy.org/

---

## License

This project is part of the Diabetes Risk Prediction System.

