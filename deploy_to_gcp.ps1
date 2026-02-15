$PROJECT_ID = "nexus-dyron-777"
$GCLOUD_PATH = "C:\Users\Danteh\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

# Function to run gcloud
function Run-GCloud {
    param([string[]]$Arguments)
    & $GCLOUD_PATH $Arguments
}

Write-Host "🚀 Starting Nexus AI Cloud Deployment..." -ForegroundColor Green

# 1. Enable services
Write-Host "Enabling Google Cloud Services..."
Run-GCloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com --project $PROJECT_ID

# 1.5 Create Artifact Registry Repo
Write-Host "Ensuring Artifact Registry Repository exists..."
& $GCLOUD_PATH artifacts repositories create nexus-repo --repository-format=docker --location=us-central1 --description="Nexus AI Container Repository" --project=$PROJECT_ID 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Repository might already exist or creation failed. Continuing..." -ForegroundColor Yellow
}

# 2. Build & Deploy
Write-Host "Submitting Build to Google Cloud..."
Run-GCloud builds submit --config nexus-genesis/nexus-core/cloudbuild.yaml --project $PROJECT_ID nexus-genesis/nexus-core


Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "Check your Cloud Run console for URLs."
