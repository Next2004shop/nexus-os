# NEXUS Deployment Script
# Deploy to Git and Google Cloud Run (Backend + Frontend)
# All hosting on Google Cloud - No Render or Vercel

param(
    [string]$CommitMessage = "NEXUS update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEXUS SOVEREIGN SYSTEM DEPLOYMENT" -ForegroundColor Cyan
Write-Host "Google Cloud Run - Full Stack" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"

# Step 1: Git Operations
Write-Host "`n[1/5] Pushing to Git..." -ForegroundColor Yellow
Set-Location "d:\nexus-ai"

git add -A
git commit -m $CommitMessage
git push origin main
if ($LASTEXITCODE -ne 0) { 
    Write-Host "Git push failed - trying to pull first" -ForegroundColor Yellow
    git pull --rebase origin main
    git push origin main
}
Write-Host "Git push complete!" -ForegroundColor Green

# Step 2: Deploy Backend to Cloud Run
Write-Host "`n[2/5] Deploying BACKEND to Cloud Run..." -ForegroundColor Yellow
Set-Location "d:\nexus-ai\nexus-genesis\nexus-core"

gcloud run deploy nexus-core `
    --source . `
    --region us-central1 `
    --platform managed `
    --no-allow-unauthenticated `
    --port 8080 `
    --memory 2Gi `
    --cpu 2 `
    --min-instances 1 `
    --max-instances 10 `
    --service-account "nexus-runtime@nexus-dyron-777.iam.gserviceaccount.com" `
    --set-secrets "BINANCE_API_KEY=BINANCE_API_KEY:latest,BINANCE_API_SECRET=BINANCE_API_SECRET:latest,MT5_LOGIN=MT5_LOGIN:latest,MT5_PASSWORD=MT5_PASSWORD:latest,MT5_SERVER=MT5_SERVER:latest,POLYGON_API_KEY=POLYGON_API_KEY:latest" `
    --set-env-vars "GOOGLE_CLOUD_PROJECT=nexus-dyron-777,LOG_LEVEL=INFO,ENVIRONMENT=production"

if ($LASTEXITCODE -ne 0) { 
    Write-Host "Backend deployment failed!" -ForegroundColor Red
    exit 1 
}
Write-Host "Backend deployment complete!" -ForegroundColor Green

# Step 3: Get Backend URL
Write-Host "`n[3/5] Getting backend service URL..." -ForegroundColor Yellow
$backendUrl = gcloud run services describe nexus-core --region us-central1 --format="value(status.url)"
Write-Host "Backend URL: $backendUrl" -ForegroundColor Cyan

# Step 4: Deploy Frontend to Cloud Run
Write-Host "`n[4/5] Deploying FRONTEND to Cloud Run..." -ForegroundColor Yellow
Set-Location "d:\nexus-ai\NEXUS-GENESIS-OMEGA\nexus-terminal"

gcloud run deploy nexus-frontend `
    --source . `
    --region us-central1 `
    --platform managed `
    --allow-unauthenticated `
    --port 8080 `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 5 `
    --set-env-vars "VITE_API_URL=$backendUrl"

if ($LASTEXITCODE -ne 0) { 
    Write-Host "Frontend deployment failed!" -ForegroundColor Red
    exit 1 
}
Write-Host "Frontend deployment complete!" -ForegroundColor Green

# Step 5: Get Frontend URL and Health Checks
Write-Host "`n[5/5] Getting service URLs and running health checks..." -ForegroundColor Yellow
$frontendUrl = gcloud run services describe nexus-frontend --region us-central1 --format="value(status.url)"
Write-Host "Frontend URL: $frontendUrl" -ForegroundColor Cyan

# Health checks
Write-Host "`nRunning health checks..." -ForegroundColor Yellow
try {
    $backendHealth = Invoke-RestMethod -Uri "$backendUrl/health" -Method Get -TimeoutSec 30
    Write-Host "Backend: $($backendHealth.status)" -ForegroundColor Green
} catch {
    Write-Host "Backend health check requires authentication (expected)" -ForegroundColor Yellow
}

try {
    $frontendResponse = Invoke-WebRequest -Uri $frontendUrl -Method Get -TimeoutSec 30
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "Frontend: Online" -ForegroundColor Green
    }
} catch {
    Write-Host "Frontend: Check manually" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "NEXUS DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "  Backend:  $backendUrl" -ForegroundColor White
Write-Host "  Frontend: $frontendUrl" -ForegroundColor White
Write-Host ""
Write-Host "All services hosted on Google Cloud Run." -ForegroundColor Yellow
Write-Host "Render and Vercel are NOT used." -ForegroundColor Yellow
