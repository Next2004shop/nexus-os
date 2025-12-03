# Nexus AI - Cloud VM Update Script (v2.1 - Data Fix)
# Run this in PowerShell on your Google Cloud VM

Write-Host "🚀 UPDATING NEXUS AI (DATA FIX)..." -ForegroundColor Cyan

# 1. Stop Existing Processes
Write-Host "🛑 Stopping running services..." -ForegroundColor Yellow
Stop-Process -Name "python" -ErrorAction SilentlyContinue
Stop-Process -Name "node" -ErrorAction SilentlyContinue

# 2. Update Code
Write-Host "⬇️ Pulling latest code from Git..." -ForegroundColor Yellow
Set-Location "C:\nexus-os"
git pull

# 2.5 Build Web App (Frontend)
Write-Host "🏗️ Building Web Application..." -ForegroundColor Yellow
npm install
npm run build

# 3. Start the Brain (Python Bridge)
Write-Host "🧠 Starting Nexus Brain (New Candles Endpoint)..." -ForegroundColor Green
Start-Process -FilePath "C:\Python311\python.exe" -ArgumentList "nexus_bridge.py" -WindowStyle Minimized

# 4. Start the Body (Node.js Server)
Write-Host "🌐 Starting Nexus Server..." -ForegroundColor Green
Start-Process -FilePath "node" -ArgumentList "server.cjs" -WindowStyle Minimized

Write-Host "✅ UPDATE COMPLETE! Charts and Wallet should now be LIVE." -ForegroundColor Cyan
Write-Host "You can close this window."
Start-Sleep -Seconds 5
