$PROJECT_ID = "project-bd8c584b-bec0-462d-850" # Found from historical config

Write-Host "🚀 Starting Nexus AI Cloud Deployment..." -ForegroundColor Green

# 1. Enable Services
Write-Host "Enabling Google Cloud Services..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com

# 2. Build & Deploy using Cloud Build
Write-Host "Submitting Build to Google Cloud..."
gcloud builds submit --config nexus-cloud/deployment/cloudbuild.yaml --project $PROJECT_ID .

Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "Check your Cloud Run console for URLs."
