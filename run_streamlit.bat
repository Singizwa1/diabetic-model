@echo off
REM Streamlit Diabetes Prediction App - Windows Batch Runner
REM This script sets up and runs the Streamlit app

cls
echo ======================================================================
echo.
echo         ^(o_o^) DIABETES RISK PREDICTION - STREAMLIT DEPLOYMENT
echo.
echo ======================================================================
echo.

REM Check if venv exists
if not exist ".venv" (
    echo [ERROR] Virtual environment not found. Please run:
    echo         python -m venv .venv
    pause
    exit /b 1
)

REM Install dependencies if needed
echo [1/3] Ensuring dependencies are installed...
call .\.venv\Scripts\python.exe -m pip install -q streamlit requests pandas 2>nul

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies ready
echo.

REM Check if FastAPI server is running
echo [2/3] Checking FastAPI backend status...
.\.venv\Scripts\python.exe -c "import requests; requests.get('http://127.0.0.1:8000/health', timeout=2)" 2>nul

if errorlevel 1 (
    echo.
    echo [!] WARNING: FastAPI server is not running!
    echo.
    echo You need to start the FastAPI server in a separate terminal:
    echo   uvicorn app.main:app --reload
    echo.
    echo The Streamlit app will still start, but predictions won't work
    echo until the API server is running.
    echo.
    pause
) else (
    echo [OK] FastAPI server is running!
)

echo.
echo [3/3] Starting Streamlit app...
echo.
echo ======================================================================
echo.
echo   ^>^> Open your browser at: http://localhost:8501
echo.
echo   Press CTRL+C to stop the app
echo.
echo ======================================================================
echo.

REM Run streamlit
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --logger.level=info

pause
