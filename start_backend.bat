@echo off
echo Starting Nexus Cloud Backend (FastAPI)...
cd nexus-cloud/backend
python -m uvicorn app.main:app --reload --port 5001
pause
