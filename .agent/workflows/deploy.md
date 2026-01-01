---
description: Deploy NEXUS to Git and Google Cloud
---

# NEXUS Deployment Workflow

This workflow pushes changes to Git and deploys to Google Cloud Run.

## Prerequisites (One-Time Setup)

Run these commands in PowerShell to set up secrets and service account:

```powershell
# Set project
gcloud config set project nexus-dyron-777

# Create Artifact Registry repository (one-time)
gcloud artifacts repositories create nexus-repo --repository-format=docker --location=us-central1

# Create service account (one-time)
gcloud iam service-accounts create nexus-runtime --display-name="NEXUS Runtime"

# Grant permissions to service account
gcloud projects add-iam-policy-binding nexus-dyron-777 --member="serviceAccount:nexus-runtime@nexus-dyron-777.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
gcloud projects add-iam-policy-binding nexus-dyron-777 --member="serviceAccount:nexus-runtime@nexus-dyron-777.iam.gserviceaccount.com" --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding nexus-dyron-777 --member="serviceAccount:nexus-runtime@nexus-dyron-777.iam.gserviceaccount.com" --role="roles/datastore.user"

# Create secrets (replace YOUR_KEY with actual values)
gcloud secrets create BINANCE_API_KEY --replication-policy="automatic"
echo -n "YOUR_BINANCE_API_KEY" | gcloud secrets versions add BINANCE_API_KEY --data-file=-

gcloud secrets create BINANCE_API_SECRET --replication-policy="automatic"
echo -n "YOUR_BINANCE_SECRET" | gcloud secrets versions add BINANCE_API_SECRET --data-file=-

gcloud secrets create MT5_LOGIN --replication-policy="automatic"
echo -n "YOUR_MT5_LOGIN" | gcloud secrets versions add MT5_LOGIN --data-file=-

gcloud secrets create MT5_PASSWORD --replication-policy="automatic"
echo -n "YOUR_MT5_PASSWORD" | gcloud secrets versions add MT5_PASSWORD --data-file=-

gcloud secrets create MT5_SERVER --replication-policy="automatic"
echo -n "YOUR_MT5_SERVER" | gcloud secrets versions add MT5_SERVER --data-file=-

gcloud secrets create POLYGON_API_KEY --replication-policy="automatic"
echo -n "YOUR_POLYGON_KEY" | gcloud secrets versions add POLYGON_API_KEY --data-file=-
```

## Deploy Workflow

// turbo-all

1. Navigate to project root:
```powershell
cd d:\nexus-ai
```

2. Add all changes to git:
```powershell
git add -A
```

3. Commit with message:
```powershell
git commit -m "NEXUS update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
```

4. Push to remote:
```powershell
git push origin main
```

5. Navigate to nexus-core:
```powershell
cd d:\nexus-ai\nexus-genesis\nexus-core
```

6. Deploy to Cloud Run:
```powershell
gcloud builds submit --config cloudbuild.yaml .
```

7. Verify deployment:
```powershell
gcloud run services describe nexus-core --region us-central1 --format="value(status.url)"
```
