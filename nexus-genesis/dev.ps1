# NEXUS SOVEREIGN SYSTEM — IGNITION SCRIPT
Write-Host "INITIALIZING NEXUS PROTOCOL..." -ForegroundColor Cyan

# 1. Start Nexus Core (Backend)
Write-Host "BOOTING BODY: Nexus Core (FastAPI) on port 8080..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd nexus-core; uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"

# 2. Start Nexus Terminal (Frontend)
Write-Host "BOOTING FACE: Nexus Terminal (Vite) on port 5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd nexus-terminal; npm run dev"

Write-Host "SYSTEM IGNITION COMPLETE. HANDSHAKE PENDING." -ForegroundColor Cyan
