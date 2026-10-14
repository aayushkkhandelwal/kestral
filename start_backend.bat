@echo off
echo ==========================================
echo Starting Kestral Vision Intelligence Backend
echo ==========================================
cd /d "%~dp0backend"
if exist ".venv\Scripts\python.exe" (
    echo Using backend virtual environment...
    ".venv\Scripts\python.exe" -u -m uvicorn main:app --host 0.0.0.0 --port 8000
) else if exist "..\.venv\Scripts\python.exe" (
    echo Using root virtual environment...
    "..\.venv\Scripts\python.exe" -u -m uvicorn main:app --host 0.0.0.0 --port 8000
) else (
    echo Using system Python...
    python -u -m uvicorn main:app --host 0.0.0.0 --port 8000
)
pause
