# 🏥 Streamlit Deployment Guide - Diabetes Risk Prediction System

Complete guide to deploy and run the Streamlit UI for the diabetes prediction system.

## Quick Start (Windows)

### Option 1: Batch File (Easiest)
```bash
run_streamlit.bat
```

This will:
1. ✅ Check the virtual environment
2. ✅ Install Streamlit and dependencies
3. ✅ Verify FastAPI server is running
4. ✅ Start Streamlit app automatically

### Option 2: PowerShell
```powershell
.\run_streamlit.ps1
```

### Option 3: Command Line
```bash
Set-Location "c:\Users\highe\OneDrive\Desktop\Model"
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

## Prerequisites

1. **Virtual Environment Active:**
   ```bash
   .\.venv\Scripts\Activate.ps1
   ```

2. **FastAPI Server Running** (in a separate terminal):
   ```bash
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```
   - API runs on: http://127.0.0.1:8000
   - Docs at: http://127.0.0.1:8000/docs

3. **Required Python Packages:**
   - streamlit==1.40.2
   - requests==2.32.3
   - pandas==2.2.3
   - (already in requirements.txt)

## Accessing the App

After running the startup script:

### Local Access
- **URL:** http://localhost:8501
- **Device:** Your computer only

### Network Access
- **URL:** http://<your-ip>:8501
- **Devices:** Other computers on your network
- **Note:** Replace `<your-ip>` with your machine's IP address

To find your IP:
```powershell
ipconfig
# Look for IPv4 Address under your active network
```

## Streamlit Interface Features

### 1. 🔮 Make Prediction
- Enter patient information:
  - BMI (10-60)
  - Body Temperature (35-40°C)
  - Lifestyle (active, moderate, sedentary, unhealthy)
  - Optional: Urination Frequency
- Get instant risk assessment
- View color-coded risk level (Low/Medium/High)
- See probability score

### 2. 📊 Model Metrics
- View all model performance metrics:
  - Accuracy, Precision, Recall
  - F1-Score, ROC-AUC
- Compare all trained models
- See visualizations (bar charts)
- Check training timestamp

### 3. ➕ Add Training Data
- Add new labeled patient data
- Input fields:
  - BMI
  - Temperature
  - Lifestyle
  - Diabetes Status (Yes/No)
  - Optional: Urination Frequency
- Data stored for retraining

### 4. 🔄 Retrain Model
- Retrain with base data + new records
- Automatic model comparison
- Select best model by F1-score
- View updated metrics
- Progress tracking

### 5. ℹ️ About
- System documentation
- Feature explanation
- Usage guide
- API endpoints reference
- Model metrics explanation

## Two-Terminal Setup

### Terminal 1: FastAPI Backend
```bash
Set-Location "c:\Users\highe\OneDrive\Desktop\Model"
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Terminal 2: Streamlit Frontend
```bash
Set-Location "c:\Users\highe\OneDrive\Desktop\Model"
.\run_streamlit.bat
REM or
.\run_streamlit.ps1
REM or
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

**Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://<ip>:8501
```

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  WEB BROWSER                        │
│              (http://localhost:8501)                │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│           STREAMLIT FRONTEND (streamlit_app.py)     │
│  - Patient input form                              │
│  - Metrics visualization                           │
│  - Data management interface                       │
└──────────────────────┬──────────────────────────────┘
                       │
            HTTP API Calls (requests)
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│      FASTAPI BACKEND (app/main.py)                 │
│      Endpoints:                                     │
│  - POST /predict                                   │
│  - POST /add-data                                  │
│  - POST /retrain                                   │
│  - GET  /metrics                                   │
│  - GET  /health                                    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│     ML PIPELINE & MODEL MANAGEMENT                  │
│  - app/preprocessing.py                            │
│  - app/feature_engineering.py                      │
│  - app/model.py (training & evaluation)            │
│  - saved_model/model.pkl (best model artifact)    │
└─────────────────────────────────────────────────────┘
```

## Troubleshooting

### Issue: "Cannot connect to API"
**Solution:** Make sure FastAPI server is running in another terminal
```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Issue: "ModuleNotFoundError: No module named 'streamlit'"
**Solution:** Install dependencies
```bash
.\.venv\Scripts\python.exe -m pip install streamlit requests
```

### Issue: Port 8501 already in use
**Solution:** Use a different port
```bash
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8502
```

### Issue: Port 8000 already in use (FastAPI)
**Solution:** Use a different port
```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
```

Then update the Streamlit app to use the new API URL.

### Issue: Model file not found
**Solution:** Train the model first
```bash
.\.venv\Scripts\python.exe -m app.model
# or
# Use Streamlit interface: 🔄 Retrain Model
```

## Performance Optimization

### For Production Deployment

1. **Remove hot reload (development mode):**
   ```bash
   .\.venv\Scripts\python.exe -m uvicorn app.main:app
   ```

2. **Use more workers:**
   ```bash
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --workers 4
   ```

3. **Streamlit optimizations:**
   - Add to `~/.streamlit/config.toml`:
   ```toml
   [client]
   showErrorDetails = false
   
   [logger]
   level = "error"
   
   [server]
   maxUploadSize = 200
   ```

4. **Use Streamlit Cloud:**
   - Create account at https://streamlit.io/cloud
   - Push code to GitHub
   - Deploy from Streamlit Cloud dashboard

## Network Sharing

To allow other users to access the app:

1. Find your IP address:
   ```powershell
   ipconfig
   ```

2. Share this URL with others:
   ```
   http://<your-ip>:8501
   ```

3. Make sure your firewall allows port 8501:
   - Windows Defender Firewall → Allow an app

## Data Storage

- **Training data:** `data/dataset-diabete.xlsx`
- **New labeled data:** `data/new_data.csv`
- **Saved model:** `saved_model/model.pkl`
- **Dataset info:** `data/` directory

## Next Steps

1. ✅ Start FastAPI backend
2. ✅ Start Streamlit frontend
3. ✅ Open http://localhost:8501
4. ✅ Enter patient data and make predictions
5. ✅ View model metrics
6. ✅ Add new training data
7. ✅ Retrain model with new data

## Support

For issues or questions:
1. Check API health: http://localhost:8000/health
2. View API docs: http://localhost:8000/docs
3. Check Streamlit logs in terminal
4. Verify virtual environment is activated

## File Structure

```
Model/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── model.py                # Model training
│   ├── preprocessing.py        # Data cleaning
│   ├── feature_engineering.py  # Feature creation
│   ├── retrain.py             # Retraining logic
│   └── utils.py               # Utility functions
├── data/
│   ├── dataset-diabete.xlsx   # Base training data
│   └── new_data.csv           # Appended labeled data
├── saved_model/
│   └── model.pkl              # Trained model artifact
├── streamlit_app.py           # Streamlit UI
├── run_streamlit.bat          # Windows batch runner
├── run_streamlit.ps1          # PowerShell runner
├── run_streamlit.py           # Python runner
├── requirements.txt           # Dependencies
├── README.md                  # Main documentation
└── STREAMLIT_DEPLOYMENT.md   # This file
```

---

**Happy Predicting! 🏥✨**
