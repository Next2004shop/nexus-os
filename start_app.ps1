# Nexus AI Startup Script
# Starts Backend, Python Bridge, and Frontend

Write-Host "🚀 INITIALIZING NEXUS AI SYSTEM..." -ForegroundColor Cyan

# 1. Start Python Bridge (MT5 Connection + Vertex AI)
Write-Host "Starting Python Bridge (Neural Core)..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "nexus_bridge.py" -WorkingDirectory "$PSScriptRoot" -WindowStyle Minimized
Write-Host "✅ Python Bridge Started." -ForegroundColor Green

# 2. Start Node.js Backend (Server Agent)
Write-Host "Starting Node.js Server (Host Agent)..." -ForegroundColor Yellow
Start-Process -FilePath "node" -ArgumentList "server.cjs" -WorkingDirectory "$PSScriptRoot" -WindowStyle Minimized
Write-Host "✅ Node.js Server Started." -ForegroundColor Green

# 3. Start Frontend (React App)
Write-Host "Starting Frontend Interface..." -ForegroundColor Yellow
# Using npm run dev for development mode as requested for "laptop app"
Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory "$PSScriptRoot" -WindowStyle Normal
Write-Host "✅ Frontend Launching..." -ForegroundColor Green

Write-Host "------------------------------------------------"
Write-Host "🎉 SYSTEM ONLINE. ACCESS APP AT: http://localhost:5173" -ForegroundColor Cyan
Write-Host "------------------------------------------------"
Write-Host "Press any key to exit this launcher (Background processes will continue)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
