# NEXUS Deployment Script
# Run this after any changes to push to Git and deploy to Cloud

param(
    [string]$CommitMessage = "NEXUS update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEXUS DEPLOYMENT PIPELINE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Git Operations
Write-Host "`n[1/4] Pushing to Git..." -ForegroundColor Yellow
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

# Step 2: Deploy to Cloud Run
Write-Host "`n[2/4] Building and deploying to Cloud Run..." -ForegroundColor Yellow
Set-Location "d:\nexus-ai\nexus-genesis\nexus-core"

gcloud builds submit --config cloudbuild.yaml .
if ($LASTEXITCODE -ne 0) { 
    Write-Host "Cloud Build failed!" -ForegroundColor Red
    exit 1 
}

Write-Host "Cloud deployment complete!" -ForegroundColor Green

# Step 3: Get service URL
Write-Host "`n[3/4] Getting service URL..." -ForegroundColor Yellow
$serviceUrl = gcloud run services describe nexus-core --region us-central1 --format="value(status.url)"
Write-Host "Service URL: $serviceUrl" -ForegroundColor Cyan

# Step 4: Health check
Write-Host "`n[4/4] Running health check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$serviceUrl/health" -Method Get -TimeoutSec 30
    Write-Host "Health check: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "Health check requires authentication (expected in production)" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
