# Diabetes Risk Prediction System - Backend API

> **Full-Stack Machine Learning Application** with FastAPI, PostgreSQL, Redis, and Swagger Documentation

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.8-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📋 Overview

A **production-ready REST API** for diabetes risk prediction featuring:

- ✅ **31+ REST API endpoints** with Swagger UI (`/docs`)
- ✅ **Redis-based token authentication** (server-side sessions, instant logout)
- ✅ **PostgreSQL database** with SQLAlchemy ORM (7 tables)
- ✅ **Trained ML model** (scikit-learn + XGBoost) for risk prediction
- ✅ **Email notifications** for high-risk assessments
- ✅ **Admin dashboard** for user management and statistics
- ✅ **Streamlit UI** for testing and manual assessments
- ✅ **Complete documentation** (SETUP, API examples, guides)

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Redis 5.0+

### Setup

```bash
# 1. Navigate to project
cd "C:\Users\highe\OneDrive\Desktop\Model"

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with PostgreSQL, Redis, and email settings

# 5. Run setup script
python quick_start.py

# 6. Start API server
python -m uvicorn app.main:app --reload

# 7. Access Swagger UI
# Open: http://localhost:8000/docs
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [SETUP.md](SETUP.md) | Complete installation & configuration guide |
| [API_EXAMPLES.md](API_EXAMPLES.md) | Curl & Python code examples for all endpoints |
| [Swagger UI](http://localhost:8000/docs) | Interactive API documentation (live) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Client (Mobile/Web/Streamlit)          │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  FastAPI 0.115.8 (Uvicorn Server)       │
│  ├─ /docs (Swagger UI)                  │
│  ├─ /auth/* (4 endpoints)               │
│  ├─ /profiles/* (4 endpoints)           │
│  ├─ /sessions/* (6 endpoints)           │
│  ├─ /predictions/* (3 endpoints)        │
│  ├─ /admin/* (4 endpoints)              │
│  └─ /health (2 endpoints)               │
└──────┬──────────────┬──────────────┬────┘
       │              │              │
       ▼              ▼              ▼
   ┌────────┐   ┌──────────┐   ┌─────────┐
   │ Redis  │   │PostgreSQL│   │ML Model │
   │Tokens  │   │7 Tables  │   │(sklearn)│
   └────────┘   └──────────┘   └─────────┘
```

---

## 📊 Database Schema

**7 ORM Tables**:
- `users` - User accounts with authentication
- `user_profiles` - Static health profiles (age, BMI, etc)
- `assessment_sessions` - 3-day assessment cycles
- `daily_logs` - Day-level symptom submissions
- `predictions` - ML prediction results
- `notifications` - User alerts and messages
- `model_registry` - Trained model tracking

---

## 🎯 Endpoints Summary (31+)

**Authentication (4)** | **Profiles (4)** | **Sessions (6)**
---|---|---
POST /auth/register | POST /profiles | POST /sessions
POST /auth/login | GET /profiles | GET /sessions
POST /auth/logout | GET /profiles/latest | GET /sessions/{id}
GET /auth/me | PUT /profiles/{id} | POST /sessions/{id}/daily-logs

**Predictions (3)** | **Admin (4)** | **Health (2)**
---|---|---
POST /predictions/sessions/{id}/predict | GET /admin/users | GET /health
GET /predictions/latest | PUT /admin/users/{id}/toggle-admin | GET /notifications
GET /predictions | GET /admin/models | -
| | GET /admin/statistics | -

---

## 🔐 Authentication: Redis Tokens

### Token Flow
```
User Login → Redis stores token (30-day TTL) → Bearer token returned
            ↓
Client stores token → Includes in Authorization header
            ↓
Server validates token from Redis → Executes endpoint
            ↓
User Logout → Token revoked immediately from Redis
```

**Why Redis Tokens?**
- ✅ Server-side storage (can revoke instantly)
- ✅ No "logged-out" tokens in circulation
- ✅ Better security for mobile apps
- ✅ Session control without JWT claims

---

## 💾 ML Model Integration

**Model Path**: `saved_model/model.pkl`  
**Training Data**: `data/Dataset_Diabetes_Final.xlsx`  
**Inference Service**: `app/services/ml_service.py`  
**Training Script**: `train_mobile_model.py`  

### Prediction Flow

```python
# User submits daily logs → Service aggregates features 
# → ML model predicts probability → Risk mapped to level
# → If high risk → Email alert sent automatically
```

---

## 📦 Dependencies (22 packages)

| Category | Packages |
|----------|----------|
| **Web** | fastapi, uvicorn |
| **Database** | sqlalchemy, psycopg2-binary |
| **Cache** | redis |
| **Auth** | passlib[bcrypt], python-multipart |
| **Validation** | pydantic, pydantic-settings, email-validator |
| **ML** | scikit-learn, xgboost, pandas, numpy, joblib, openpyxl |
| **Utilities** | python-dotenv, requests |

See `requirements.txt` for exact versions.

---

## 🚀 Deployment Ready

- ✅ Environment-based configuration (.env)
- ✅ Database migrations (auto-create tables)
- ✅ Logging and error handling
- ✅ CORS middleware configured
- ✅ Health check endpoint
- ✅ Docker-ready structure

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Redis connection failed | Ensure Redis is running: `redis-cli ping` |
| PostgreSQL error | Check DATABASE_URL in .env, verify service running |
| ML model not loading | Verify `saved_model/model.pkl` exists and permissions |
| CORS error | Update `allow_origins` in `app/main.py` |
| Token expired | Login again with `/auth/login` to get new token |

---

## 📖 Directory Structure

```
.
├── app/                    # Main application
│   ├── main.py            # FastAPI app factory
│   ├── models.py          # SQLAlchemy ORM (7 tables)
│   ├── schemas.py         # Pydantic validation
│   ├── database.py        # SQLAlchemy Base
│   ├── cache.py           # Redis token manager
│   ├── core/
│   │   ├── config.py      # Settings from .env
│   │   └── security.py    # Password & auth
│   ├── routes/            # 31+ API endpoints
│   ├── services/          # Business logic
│   └── mobile_training.py # ML pipeline
├── saved_model/
│   └── model.pkl          # Trained model ✓
├── data/
│   └── Dataset_Diabetes_Final.xlsx  # Training data ✓
├── streamlit_app.py       # Web UI ✓
├── quick_start.py         # Setup automation
├── train_mobile_model.py  # Retraining script ✓
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── SETUP.md              # Installation guide
├── API_EXAMPLES.md       # Usage examples
└── README.md             # This file
```

---

## ✨ Key Features

- **🔐 Secure**: Bcrypt hashing, token validation, SQL injection protection
- **⚡ Fast**: Async FastAPI, connection pooling
- **🎯 ML Ready**: Integrated scikit-learn/XGBoost models
- **📧 Smart**: Auto-sends high-risk alerts via email
- **👨‍💼 Admin**: User management, statistics, model registry
- **📊 Observable**: Logging, health checks, metrics
- **🔄 Scalable**: Redis for horizontal scaling, PostgreSQL backups

---

## 📝 Getting Help

1. Check [SETUP.md](SETUP.md) for installation issues
2. See [API_EXAMPLES.md](API_EXAMPLES.md) for code samples
3. Visit Swagger UI at `http://localhost:8000/docs` for interactive testing
4. Check logs in terminal for error messages

---

## 📄 License

MIT License - This project is open source and free to use.

---

**🎉 Full-featured diabetes risk prediction API - Ready for production!**

You need TWO terminals running simultaneously:

**Terminal 1 - FastAPI Backend:**
```bash
Set-Location "c:\Users\highe\OneDrive\Desktop\Model"
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```
- Runs on: http://127.0.0.1:8000
- API Documentation: http://127.0.0.1:8000/docs

**Terminal 2 - Streamlit Frontend:**
```bash
Set-Location "c:\Users\highe\OneDrive\Desktop\Model"
.\run_streamlit.bat
```
- Runs on: http://localhost:8501
- Interactive UI for predictions, metrics, and retraining

Both terminals should show:
- FastAPI: "Uvicorn running on http://127.0.0.1:8000"
- Streamlit: "You can now view your Streamlit app in your browser"

## Required Dataset

Place your Excel file at:

data/diabetes.xlsx

The file should contain:
- dataset sheet: data rows
- codebook sheet: metadata (not used in training)

Required columns (in dataset sheet, case-insensitive):
- bmi
- temperature
- lifestyle
- diabetes

Optional:
- urination_frequency (generated automatically if missing)

## API Endpoints

1. POST /predict

Input:
{
  "bmi": 29.1,
  "temperature": 37.1,
  "lifestyle": "sedentary"
}

Output:
{
  "risk_level": "Medium",
  "probability": 0.6123
}

2. POST /add-data

Input:
{
  "bmi": 31.2,
  "temperature": 37.0,
  "lifestyle": "inactive",
  "diabetes": 1
}

3. POST /retrain

Retrains using base Excel + data/new_data.csv and saves best model.

4. GET /metrics

Returns best model name and full metric comparison table.

## Risk Logic

- probability < 0.30  -> Low
- 0.30 to <0.70       -> Medium
- >= 0.70             -> High

## Streamlit UI Features

### 🔮 Make Prediction
- Enter patient BMI, temperature, and lifestyle
- Get instant risk prediction
- View color-coded risk level with probability
- See input summary

### 📊 Model Metrics
- View all model performance metrics
- See model comparison table
- Visualize metrics (accuracy, F1-score, etc.)
- Check training timestamp

### ➕ Add Training Data
- Add new labeled patient records
- Input patient features and diabetes status
- Data stored for future retraining

### 🔄 Retrain Model
- Retrain with base data + new records
- Automatic model comparison
- View updated performance metrics
- Real-time progress tracking

### ℹ️ About
- System documentation
- Feature explanations
- Usage guide and API reference
- Data flow diagram

## Notes

- If no model file exists, call /retrain first
- /predict can optionally receive urination_frequency; if omitted, backend generates it dynamically
- For detailed deployment info, see: [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)
