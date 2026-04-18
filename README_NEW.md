# 🏥 Diabetes Risk Prediction System

A complete, production-ready diabetes risk prediction system with **FastAPI backend**, **Streamlit web UI**, and **machine learning models**.

## ✨ Features

✅ **FastAPI REST API** - RESTful endpoints for predictions  
✅ **Streamlit Web UI** - Interactive dashboard with 5 pages  
✅ **Three ML Models** - Logistic Regression, Random Forest, XGBoost  
✅ **Automatic Model Selection** - Best model chosen by F1-score  
✅ **Auto-Retraining** - Update model with new labeled data  
✅ **Risk Classification** - Low/Medium/High risk levels  
✅ **Real-time Metrics** - View model performance metrics  
✅ **Data Management** - Add and track new predictions  

## 📁 Project Structure

```
Model/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── model.py                # Model training & evaluation
│   ├── preprocessing.py        # Data cleaning pipeline
│   ├── feature_engineering.py  # Feature creation from raw data
│   ├── retrain.py             # Retraining logic
│   └── utils.py               # Utility functions
├── data/
│   ├── dataset-diabete.xlsx   # Base training data (1000 rows)
│   └── new_data.csv           # Appended labeled rows for retraining
├── saved_model/
│   └── model.pkl              # Trained model artifact
├── streamlit_app.py           # Streamlit web interface
├── run_streamlit.bat          # Windows batch startup script
├── run_streamlit.ps1          # PowerShell startup script
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── STREAMLIT_DEPLOYMENT.md   # Detailed deployment guide
```

## 🚀 Quick Start

### 1. Create Virtual Environment

```bash
cd "c:\Users\highe\OneDrive\Desktop\Model"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Both Servers (Two Terminals)

**Terminal 1 - FastAPI Backend:**
```bash
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```
Output: `Uvicorn running on http://127.0.0.1:8000`

**Terminal 2 - Streamlit Frontend:**
```bash
.\run_streamlit.bat
```
Output: `Open http://localhost:8501`

## 📊 Streamlit UI Pages

### 🔮 Make Prediction
- Enter patient information (BMI, temperature, lifestyle)
- Get instant diabetes risk prediction
- View color-coded risk level (Low/Medium/High)
- See prediction probability and interpretation

### 📊 Model Metrics
- View best model performance
- See all metrics: Accuracy, Precision, Recall, F1-Score, ROC-AUC
- Compare all three trained models
- View visualizations (charts)

### ➕ Add Training Data
- Add new labeled patient records
- Input: BMI, temperature, lifestyle, diabetes status
- Stores data for future retraining
- Optional: urination frequency

### 🔄 Retrain Model
- Retrain model with base data + new records
- Automatic model comparison
- Select best model by F1-score
- View updated metrics

### ℹ️ About
- System documentation
- Feature explanation
- Usage guide
- API endpoints reference

## 🔌 REST API Endpoints

### Health Check
```http
GET http://127.0.0.1:8000/health
```

### Make Prediction
```http
POST http://127.0.0.1:8000/predict
Content-Type: application/json

{
  "bmi": 29.1,
  "temperature": 37.0,
  "lifestyle": "sedentary",
  "urination_frequency": 8
}
```

**Response:**
```json
{
  "risk_level": "Medium",
  "probability": 0.6234
}
```

### Add Training Data
```http
POST http://127.0.0.1:8000/add-data
Content-Type: application/json

{
  "bmi": 31.2,
  "temperature": 37.0,
  "lifestyle": "inactive",
  "diabetes": 1,
  "urination_frequency": 10
}
```

### Retrain Model
```http
POST http://127.0.0.1:8000/retrain
```

### Get Metrics
```http
GET http://127.0.0.1:8000/metrics
```

### Interactive API Docs
```
http://127.0.0.1:8000/docs
```

## 🏥 Risk Interpretation

| Probability | Risk Level | Interpretation |
|------------|-----------|-----------------|
| 0.0 - 0.30 | 🟢 Low | Continue healthy lifestyle |
| 0.30 - 0.70 | 🟡 Medium | Modify lifestyle, regular checkups |
| 0.70 - 1.0 | 🔴 High | Consult healthcare professional |

## 📈 Model Performance

The system trains and compares three models:

1. **Logistic Regression** - Fast, interpretable
2. **Random Forest** - Robust, captures non-linearity
3. **XGBoost** - ⭐ Often best, gradient boosting

**Best model is automatically selected based on F1-score.**

### Key Metrics Tracked
- **Accuracy** - Overall correctness
- **Precision** - Positive prediction accuracy
- **Recall** - True positive detection rate
- **F1-Score** - Harmonic mean (used for selection)
- **ROC-AUC** - Area under ROC curve

## 🔄 Data Flow

```
Raw Data (Excel)
       ↓
Feature Engineering
  - BMI from height/weight
  - Temperature from activity
  - Lifestyle from behaviors
  - Urination frequency from risk factors
       ↓
Data Cleaning
  - Handle missing values
  - Remove duplicates
  - Standardize columns
       ↓
Preprocessing
  - Numeric: StandardScaler
  - Categorical: OneHotEncoder
       ↓
Train/Test Split (80/20)
       ↓
Model Training & Comparison
  - Logistic Regression
  - Random Forest
  - XGBoost
       ↓
Select Best Model (by F1-score)
       ↓
Save Model Artifact
       ↓
API Predictions
```

## 📥 Required Dataset Format

Place your Excel file at: `data/dataset-diabete.xlsx`

**Required columns:**
- `Age` - Patient age
- `Sex` - Gender (1/2)
- `Ht` - Height (cm)
- `Wt` - Weight (kg)
- `Activity` - Activity level (0/1)
- `Alcohol` - Alcohol consumption (0/1)
- `Smoking` - Smoking status (0/1)
- Other health indicators

**Features are automatically engineered from raw data.**

## ✅ Installation Checklist

- [ ] Virtual environment created and activated
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Excel dataset placed at `data/dataset-diabete.xlsx`
- [ ] FastAPI server running: `uvicorn app.main:app --reload`
- [ ] Streamlit app running: `.\run_streamlit.bat`
- [ ] Browser opened to `http://localhost:8501`
- [ ] API health check passed: `http://127.0.0.1:8000/health`

## 🔧 Startup Scripts

### Windows Batch (Easiest)
```bash
run_streamlit.bat
```
✅ Checks virtual environment  
✅ Installs dependencies  
✅ Verifies FastAPI server  
✅ Starts Streamlit app  

### PowerShell
```powershell
.\run_streamlit.ps1
```

### Manual Command Line
```bash
.\.venv\Scripts\python -m streamlit run streamlit_app.py
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot connect to API" | Start FastAPI: `uvicorn app.main:app --reload` |
| "ModuleNotFoundError: streamlit" | Install: `pip install streamlit requests` |
| Port 8501 in use | Use different port: `streamlit run streamlit_app.py --server.port 8502` |
| Port 8000 in use | Use different port: `uvicorn app.main:app --port 8001` |
| Model not found | Train model: Use Streamlit `🔄 Retrain Model` page |
| API returns 503 error | Model not loaded. Run `/retrain` endpoint first |

## 📚 Documentation

- **[STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)** - Detailed deployment guide
- **[API Interactive Docs](http://127.0.0.1:8000/docs)** - Swagger UI
- **[README.md](README.md)** - Project overview (this file)

## 🎯 Usage Examples

### Example 1: Make a Prediction via Streamlit UI
1. Open http://localhost:8501
2. Go to "🔮 Make Prediction"
3. Enter: BMI=28.5, Temperature=37.0, Lifestyle="moderate"
4. Click "Get Prediction"
5. View risk level and probability

### Example 2: Make a Prediction via API
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"bmi": 28.5, "temperature": 37.0, "lifestyle": "moderate"}'
```

### Example 3: Retrain Model
1. Add new labeled data via Streamlit "➕ Add Training Data"
2. Go to "🔄 Retrain Model"
3. Click "Start Retraining"
4. View updated metrics

## 🌐 Network Access

To access from another computer:

1. Find your IP: `ipconfig | grep IPv4`
2. Share URL: `http://<your-ip>:8501`
3. Ensure firewall allows port 8501

## 📦 Dependencies

```
fastapi==0.115.8          # Web framework
uvicorn==0.30.6           # ASGI server
streamlit==1.40.2         # Web UI
pandas==2.2.3             # Data manipulation
openpyxl==3.1.5          # Excel reader
scikit-learn==1.5.2       # ML models
xgboost==2.1.1           # Gradient boosting
joblib==1.4.2            # Model persistence
numpy==2.1.1             # Numerical computing
pydantic==2.9.2           # Data validation
requests==2.32.3         # HTTP client
```

## 🚢 Deployment Options

### Local Development
```bash
./run_streamlit.bat  # Runs on http://localhost:8501
```

### Production Server
See [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md) for:
- Multi-worker setup
- Streamlit Cloud deployment
- Docker containerization
- Network configuration

## 📝 Notes

- Model is selected based on **F1-score**
- Urination frequency is auto-generated if not provided
- All data processing is local (no external API calls)
- Model retraining combines base data + new records
- Configuration can be customized via environment variables

## 👤 User Roles

- **Patient**: Use Streamlit to get risk prediction
- **Doctor**: View metrics, add patient data, trigger retraining
- **Data Scientist**: Access API directly, train custom models

## 🎓 Educational Use

This system demonstrates:
- FastAPI REST API design
- Streamlit interactive dashboards
- scikit-learn model pipeline
- Feature engineering from raw data
- Model comparison and selection
- Deployment patterns

## 📞 Support

**Check API Status:**
```bash
curl http://127.0.0.1:8000/health
```

**View API Documentation:**
```
http://127.0.0.1:8000/docs
```

**Check Logs:**
- FastAPI logs in Terminal 1
- Streamlit logs in Terminal 2

---

**Happy Predicting! 🏥✨**

*Version 1.0.0 - April 18, 2026*
