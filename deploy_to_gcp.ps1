$PROJECT_ID = "project-bd8c584b-bec0-462d-850" # Found from historical config

Write-Host "🚀 Starting Nexus AI Cloud Deployment..." -ForegroundColor Green

# 1. Enable Services
Write-Host "Enabling Google Cloud Services..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com

# 1.5 Fix Permissions (Grant Storage Access to Compute Service Account)
Write-Host "Fixing IAM Permissions..."
$PROJECT_NUMBER = gcloud projects list --filter="projectId:$PROJECT_ID" --format="value(projectNumber)"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" --role="roles/storage.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" --role="roles/cloudbuild.builds.editor"

# 2. Build & Deploy using Cloud Build
Write-Host "Submitting Build to Google Cloud..."
# 2. Build & Deploy using Cloud Build
Write-Host "Preparing Clean Build Context..."
$STAGING_DIR = "build_staging"
# Fix for Full C: Drive (Redirect Temp to D:)
Write-Host "Redirecting TEMP to D:\nexus-ai\tmp to bypass full C: drive..."
$LOCAL_TEMP = "d:\nexus-ai\tmp"
New-Item -ItemType Directory -Path $LOCAL_TEMP -Force | Out-Null
$env:TEMP = $LOCAL_TEMP
$env:TMP = $LOCAL_TEMP

if (Test-Path $STAGING_DIR) { Remove-Item -Recurse -Force $STAGING_DIR }
New-Item -ItemType Directory -Path $STAGING_DIR | Out-Null

# Copy only necessary files to staging to avoid file lock issues
Write-Host "Copying source files to staging..."
Copy-Item -Recurse -Path "nexus-cloud" -Destination "$STAGING_DIR\nexus-cloud"
Copy-Item ".gcloudignore" -Destination "$STAGING_DIR\.gcloudignore"

# Run build from staging
Write-Host "Submitting Build to Google Cloud..."
Set-Location $STAGING_DIR
try {
    gcloud builds submit --config nexus-cloud/deployment/cloudbuild.yaml --project $PROJECT_ID .
}
finally {
    Set-Location ..
}

Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "Check your Cloud Run console for URLs."
