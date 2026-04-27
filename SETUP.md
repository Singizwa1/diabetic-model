# Diabetes Risk Prediction API - Complete Setup Guide

## Overview

This is a **production-ready FastAPI backend** for a diabetes risk prediction system with:
- ✅ **Redis-based token authentication** (server-side sessions with instant logout)
- ✅ **PostgreSQL database** with 7 ORM models
- ✅ **ML model integration** (scikit-learn + XGBoost) with trained model.pkl
- ✅ **31+ REST API endpoints** with Swagger documentation
- ✅ **Streamlit UI** for testing and manual assessments

---

## Prerequisites

Ensure you have installed:
- **Python 3.9+** ([download](https://www.python.org/downloads/))
- **PostgreSQL 13+** ([download](https://www.postgresql.org/download/))
- **Redis Server** ([download](https://redis.io/download))
- **Git** (optional, for version control)

---

## Step 1: Clone Repository and Setup Python

```bash
# Navigate to your project directory
cd C:\Users\highe\OneDrive\Desktop\Model

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Setup PostgreSQL Database

### Create Database

```bash
# Open PostgreSQL command prompt
psql -U postgres

# Create database
CREATE DATABASE diabetes_db;

# Create user (recommended for security)
CREATE USER diabetes_user WITH PASSWORD 'secure_password_here';

# Grant privileges
ALTER ROLE diabetes_user CREATEDB;
ALTER DATABASE diabetes_db OWNER TO diabetes_user;

# Exit psql
\q
```

### Verify Connection

```bash
psql -U diabetes_user -d diabetes_db -h localhost
```

If successful, you'll see the `diabetes_db=#` prompt.

---

## Step 3: Setup Redis Server

### Install Redis (Windows)

1. Download **Redis 7.0+** from [Redis Community](https://github.com/tporadowski/redis/releases)
2. Run installer and follow prompts
3. Redis will install and start automatically

### Verify Redis Connection

```bash
# Open Command Prompt
redis-cli ping
# Expected output: PONG
```

---

## Step 4: Configure Environment Variables

Create `.env` file in project root:

```bash
# Copy example
copy .env.example .env

# Edit .env with your values
```

### `.env` Template

```env
# Database
DATABASE_URL=postgresql://diabetes_user:secure_password_here@localhost:5432/diabetes_db

# Redis (for tokens and sessions)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Leave empty if no password set

# Security
SECRET_KEY=your-secret-key-here-min-32-chars-for-production

# Email (Gmail example - enable 2FA and create app password)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password  # NOT your Gmail password

# Admin User
ADMIN_EMAIL=admin@localhost
ADMIN_PASSWORD=admin123  # Change in production!

# Application
APP_NAME=Diabetes Risk Prediction API
APP_VERSION=2.0.0
ENVIRONMENT=development
```

---

## Step 5: Initialize Database and Create Admin User

```bash
# Activate virtual environment
venv\Scripts\activate

# Run quick start setup
python quick_start.py
```

Expected output:
```
============================================================
🚀 Diabetes Risk Prediction API - Quick Start Setup
============================================================

✅ All required environment variables present

📊 Setting up database tables...
✅ Database tables created successfully

🔴 Checking Redis connection...
✅ Redis connected successfully

🤖 Loading ML model...
✅ ML model loaded successfully

👤 Setting up admin user...
✅ Admin user created: admin@localhost

🏥 Running health check...
✅ Database: OK
✅ Redis: OK
✅ ML Model: OK

✅ Setup completed successfully!

📝 Next steps:
  1. Start the API: python -m uvicorn app.main:app --reload
  2. View Swagger docs: http://localhost:8000/docs
  3. Start Streamlit: streamlit run streamlit_app.py
```

---

## Step 6: Start the API Server

### Start FastAPI with Uvicorn

```bash
# Make sure venv is activated
venv\Scripts\activate

# Start development server (with hot reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Access Swagger API Docs

Open browser and navigate to:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## Step 7: Test API with Swagger

### 1. Register User

In Swagger UI (`/docs`):
1. Click **POST /auth/register**
2. Click "Try it out"
3. Enter request body:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```
4. Click "Execute"

### 2. Login and Get Token

1. Click **POST /auth/login**
2. Click "Try it out"
3. Enter credentials:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```
4. Click "Execute"
5. **Copy the `access_token` from response**

### 3. Authorize Swagger

1. Click **Authorize** button (top-right)
2. Paste token in format: `Bearer <your_token_here>`
3. Click "Authorize"

### 4. Test Other Endpoints

Now you can test endpoints like:
- **POST /profiles** - Create health profile
- **POST /sessions** - Start assessment session
- **POST /sessions/{id}/daily-logs** - Submit daily symptom log
- **POST /predictions/sessions/{id}/predict** - Run ML inference
- **GET /predictions/latest** - View latest prediction

---

## Step 8 (Optional): Start Streamlit UI for Testing

In **new terminal window**:

```bash
# Activate virtual environment
venv\Scripts\activate

# Start Streamlit
streamlit run streamlit_app.py
```

Expected output:
```
  You can now view your Streamlit app in your browser.
  
  URL: http://localhost:8501
```

---

## API Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Client (Mobile App / Streamlit / Browser)              │
│  Sends: GET/POST with Bearer Token in Authorization     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI Server (Port 8000)                             │
│  ├─ /docs (Swagger UI)                                  │
│  ├─ /auth/* (Login, Register, Logout)                   │
│  ├─ /profiles/* (Health profiles)                       │
│  ├─ /sessions/* (Assessment sessions)                   │
│  ├─ /predictions/* (ML inference results)               │
│  ├─ /admin/* (User management, statistics)              │
│  └─ /health (Status checks)                             │
└────────────┬─────────────────────────────────────────────┘
             │
    ┌────────┴──────────┬──────────────┐
    ▼                   ▼              ▼
┌─────────┐      ┌──────────┐   ┌──────────┐
│Redis    │      │PostgreSQL│   │ML Model  │
│(Tokens) │      │(Data)    │   │(Inference)
└─────────┘      └──────────┘   └──────────┘
```

---

## Database Schema

### Users Table
```
users (id, email, password_hash, full_name, is_active, is_admin, created_at)
  ├── user_profiles (user_id, age, sex, height_cm, weight_kg, bmi)
  ├── assessment_sessions (user_id, status, daily_logs[], predictions[])
  └── notifications (user_id, title, message, is_read)
```

### Session Flow
```
1. User registers → User created
2. Create profile → UserProfile created
3. Start session → AssessmentSession (status=COLLECTING)
4. Add 3 daily logs → DailyLog entries
5. Complete session → AssessmentSession (status=COMPLETED)
6. Run prediction → Prediction created, high-risk email sent
```

---

## Important Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application factory |
| `app/models.py` | SQLAlchemy ORM models (7 tables) |
| `app/schemas.py` | Pydantic request/response schemas |
| `app/cache.py` | Redis token management |
| `app/core/config.py` | Settings from .env |
| `app/core/security.py` | Password hashing, auth dependencies |
| `app/routes/` | 31+ API endpoints (auth, profiles, sessions, etc.) |
| `app/services/` | Business logic (auth, ML, email, etc.) |
| `app/database.py` | SQLAlchemy Base and engine |
| `saved_model/model.pkl` | Trained ML model (required) |
| `data/Dataset_Diabetes_Final.xlsx` | Training data for retraining |
| `requirements.txt` | Python dependencies |
| `.env` | Environment variables (CREATE THIS!) |

---

## Troubleshooting

### Redis Connection Error
```
Error: ConnectionError: Error 10061
```
**Solution**: Ensure Redis is running. Test with `redis-cli ping`

### PostgreSQL Connection Error
```
Error: could not connect to server
```
**Solution**: Check DATABASE_URL in .env, ensure PostgreSQL service is running

### ML Model Not Loading
```
Warning: ML model loading failed
```
**Solution**: Verify `saved_model/model.pkl` exists and permissions are correct

### CORS Error from Frontend
**Solution**: Update `CORSMiddleware` in `app/main.py` to include your frontend URL:
```python
allow_origins=["http://localhost:3000", "http://localhost:8501"],
```

### Token Expired
**Solution**: Tokens expire after 30 days. Login again to get new token.

---

## Production Deployment Checklist

- [ ] Change `ENVIRONMENT=production`
- [ ] Change `ADMIN_PASSWORD` to strong random value
- [ ] Set `SECRET_KEY` to 32+ random characters
- [ ] Restrict `allow_origins` in CORS to specific domains
- [ ] Setup SSL/TLS certificate for HTTPS
- [ ] Configure database backup strategy
- [ ] Setup Redis persistence (RDB or AOF)
- [ ] Enable PostgreSQL authentication
- [ ] Setup email with SMTP server (not Gmail app password)
- [ ] Setup monitoring and logging
- [ ] Run security audit on dependencies: `pip-audit`

---

## API Endpoints Summary

**Authentication (4)**
- POST `/auth/register` - Register new user
- POST `/auth/login` - Login and get Redis token
- POST `/auth/logout` - Logout and revoke token
- GET `/auth/me` - Get current user info

**Profiles (4)**
- POST `/profiles` - Create health profile
- GET `/profiles` - List user profiles
- GET `/profiles/latest` - Get latest profile
- PUT `/profiles/{id}` - Update profile

**Sessions (6)**
- POST `/sessions` - Start assessment session
- GET `/sessions` - List sessions
- GET `/sessions/{id}` - Get session details
- POST `/sessions/{id}/daily-logs` - Add daily log
- POST `/sessions/{id}/complete` - Mark complete
- POST `/sessions/{id}/cancel` - Cancel session

**Predictions (3)**
- POST `/predictions/sessions/{id}/predict` - Run ML inference
- GET `/predictions/latest` - Get latest prediction
- GET `/predictions` - List all predictions

**Admin (4)**
- GET `/admin/users` - List users
- PUT `/admin/users/{id}/toggle-admin` - Change admin status
- GET `/admin/models` - List ML models
- GET `/admin/statistics` - Get system statistics

**Health (2)**
- GET `/health` - Health check
- GET `/notifications` - Get user notifications

**Total: 31+ Endpoints**

---

## Support

For issues or questions:
1. Check logs: `python quick_start.py`
2. Verify `.env` configuration
3. Test Redis: `redis-cli ping`
4. Test PostgreSQL: `psql -U diabetes_user -d diabetes_db`
5. Test ML Model: `python -c "from app.services.ml_service import MLService; MLService().load_model()"`

---

**🎉 You're now ready to use the Diabetes Risk Prediction API!**
