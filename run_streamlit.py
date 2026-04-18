#!/usr/bin/env python
"""
Run script for the Streamlit Diabetes Prediction app.
Ensures dependencies are installed before running.
"""
import subprocess
import sys
from pathlib import Path

def run_streamlit():
    """Run the Streamlit app."""
    app_path = Path(__file__).parent / "streamlit_app.py"
    
    print("=" * 70)
    print("🏥 DIABETES RISK PREDICTION - STREAMLIT APP")
    print("=" * 70)
    print()
    print("📡 Starting Streamlit server...")
    print()
    print("🌐 Local URL:     http://localhost:8501")
    print("📊 Network URL:   http://<your-ip>:8501")
    print()
    print("Press CTRL+C to stop the server")
    print()
    print("=" * 70)
    print()
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--logger.level=info"
    ])

if __name__ == "__main__":
    run_streamlit()
