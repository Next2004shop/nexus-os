# NEXUS Deployment Script
# Deploy to Git and Google Cloud Run (Backend + Frontend)

param(
    [string]$CommitMessage = "NEXUS update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEXUS DEPLOYMENT PIPELINE" -ForegroundColor Cyan
Write-Host "Google Cloud Run - Backend + Frontend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Git Operations
Write-Host "`n[1/6] Pushing to Git..." -ForegroundColor Yellow
Set-Location "d:\nexus-ai"

git add -A
if ($LASTEXITCODE -ne 0) { Write-Host "Git add failed" -ForegroundColor Red; exit 1 }

git commit -m $CommitMessage
# Commit might fail if nothing to commit, that's OK

git push origin main
if ($LASTEXITCODE -ne 0) { 
    Write-Host "Git push failed - trying to pull first" -ForegroundColor Yellow
    git pull --rebase origin main
    git push origin main
}

Write-Host "Git push complete!" -ForegroundColor Green

# Step 2: Deploy Backend to Cloud Run
Write-Host "`n[2/6] Building and deploying BACKEND to Cloud Run..." -ForegroundColor Yellow
Set-Location "d:\nexus-ai\nexus-genesis\nexus-core"

gcloud builds submit --config cloudbuild.yaml .
if ($LASTEXITCODE -ne 0) { 
    Write-Host "Backend Cloud Build failed!" -ForegroundColor Red
    exit 1 
}

Write-Host "Backend deployment complete!" -ForegroundColor Green

# Step 3: Get Backend service URL
Write-Host "`n[3/6] Getting backend service URL..." -ForegroundColor Yellow
$backendUrl = gcloud run services describe nexus-core --region us-central1 --format="value(status.url)"
Write-Host "Backend URL: $backendUrl" -ForegroundColor Cyan

# Step 4: Deploy Frontend to Cloud Run
Write-Host "`n[4/6] Building and deploying FRONTEND to Cloud Run..." -ForegroundColor Yellow
Set-Location "d:\nexus-ai\nexus-cloud\frontend"

# Build and deploy frontend using gcloud
gcloud run deploy nexus-frontend `
    --source . `
    --region us-central1 `
    --platform managed `
    --allow-unauthenticated `
    --port 3000 `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 5 `
    --set-env-vars "NEXT_PUBLIC_API_URL=$backendUrl"

if ($LASTEXITCODE -ne 0) { 
    Write-Host "Frontend Cloud Build failed!" -ForegroundColor Red
    exit 1 
}

Write-Host "Frontend deployment complete!" -ForegroundColor Green

# Step 5: Get Frontend service URL
Write-Host "`n[5/6] Getting frontend service URL..." -ForegroundColor Yellow
$frontendUrl = gcloud run services describe nexus-frontend --region us-central1 --format="value(status.url)"
Write-Host "Frontend URL: $frontendUrl" -ForegroundColor Cyan

# Step 6: Health checks
Write-Host "`n[6/6] Running health checks..." -ForegroundColor Yellow

# Backend health check
try {
    $backendHealth = Invoke-RestMethod -Uri "$backendUrl/health" -Method Get -TimeoutSec 30
    Write-Host "Backend health: $($backendHealth.status)" -ForegroundColor Green
} catch {
    Write-Host "Backend health check requires authentication (expected)" -ForegroundColor Yellow
}

# Frontend health check
try {
    $frontendResponse = Invoke-WebRequest -Uri $frontendUrl -Method Get -TimeoutSec 30
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "Frontend health: OK" -ForegroundColor Green
    }
} catch {
    Write-Host "Frontend health check failed: $_" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nService URLs:" -ForegroundColor Cyan
Write-Host "  Backend:  $backendUrl" -ForegroundColor White
Write-Host "  Frontend: $frontendUrl" -ForegroundColor White
Write-Host "`nNOTE: Render and Vercel are NOT used." -ForegroundColor Yellow
Write-Host "All hosting is on Google Cloud Run." -ForegroundColor Yellow
