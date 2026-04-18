# Diabetes Risk Prediction System (FastAPI + scikit-learn + Streamlit)

A complete diabetes risk prediction system with FastAPI backend, Streamlit UI, and machine learning models.

## Features

✅ **FastAPI Backend** - RESTful API for predictions  
✅ **Streamlit UI** - Interactive web interface  
✅ **Three ML Models** - Logistic Regression, Random Forest, XGBoost  
✅ **Auto-Retraining** - Update model with new data  
✅ **Risk Assessment** - Classify risk levels (Low/Medium/High)  
✅ **Model Metrics** - View performance (Accuracy, F1, ROC-AUC, etc)

app/
  main.py           # FastAPI app
  model.py          # model training and evaluation
  preprocessing.py  # data loading/cleaning/preprocessing pipeline
  retrain.py        # add-data and retraining logic
  utils.py          # synthetic feature and risk mapping utilities
  feature_engineering.py  # feature creation from raw data

data/
  diabetes.xlsx     # base training dataset
  new_data.csv      # appended labeled rows for retraining

saved_model/
  model.pkl         # persisted best model artifact

streamlit_app.py    # Streamlit web UI
run_streamlit.bat   # Windows batch startup script
run_streamlit.ps1   # PowerShell startup script
run_streamlit.py    # Python runner script

## How It Works

1. Loads Excel from data/diabetes.xlsx using sheet: dataset.
2. Cleans data:
   - lowercase/snake_case columns
   - duplicate removal
   - missing handling (mean for numeric, mode for categorical)
3. Generates synthetic urination_frequency when absent.
4. Trains and compares:
   - Logistic Regression
   - Random Forest
   - XGBoost
5. Selects best model by F1-score and saves artifact in saved_model/model.pkl.
6. FastAPI endpoints expose prediction, add-data, retraining, and metrics.

## Two-Terminal Setup (Recommended)

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
