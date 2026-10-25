@echo off
title Mlzmodel Sports Biomechanics Launcher
cd /d "%~dp0"

echo ======================================================================
echo   Launching Mlzmodel: Sports Biomechanics Power Profiler
echo ======================================================================
echo.
echo Local Web Dashboard: http://localhost:8501
echo Network (Phone/Tablet on same Wi-Fi): check ipconfig for your local IPv4
echo.
echo Starting Streamlit server and opening browser...
echo Press Ctrl+C in this terminal window to stop the server.
echo.

start "" http://localhost:8501
call .venv\Scripts\streamlit run app.py --server.headless false

pause
