# Streamlit Diabetes Prediction App - PowerShell Runner
# This script sets up and runs the Streamlit app on Windows

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "         🏥 DIABETES RISK PREDICTION - STREAMLIT DEPLOYMENT" -ForegroundColor Cyan
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (-not (Test-Path ".venv")) {
    Write-Host "[ERROR] Virtual environment not found." -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Install dependencies
Write-Host "[1/3] Ensuring dependencies are installed..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pip install -q streamlit requests pandas 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Dependencies ready" -ForegroundColor Green
Write-Host ""

# Check FastAPI server
Write-Host "[2/3] Checking FastAPI backend status..." -ForegroundColor Yellow
try {
    $null = .\.venv\Scripts\python.exe -c "import requests; requests.get('http://127.0.0.1:8000/health', timeout=2)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] FastAPI server is running!" -ForegroundColor Green
    } else {
        Write-Host "[!] WARNING: FastAPI server is not running!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "You need to start the FastAPI server in a separate terminal:" -ForegroundColor Yellow
        Write-Host "  Set-Location 'c:\Users\highe\OneDrive\Desktop\Model'" -ForegroundColor White
        Write-Host "  .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload" -ForegroundColor White
        Write-Host ""
    }
} catch {
    Write-Host "[!] WARNING: Could not connect to FastAPI server" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3/3] Starting Streamlit app..." -ForegroundColor Yellow
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   >> Open your browser at: http://localhost:8501 " -ForegroundColor Green
Write-Host ""
Write-Host "   Press CTRL+C to stop the app" -ForegroundColor Yellow
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Run streamlit
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --logger.level=info
