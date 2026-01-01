# NEXUS SOVEREIGN SYSTEM

**Architecture**: Ancient Market Cycles × Axelrod Game Theory  
**Brain**: Claude-3.5-Haiku (Vertex AI)  
**Governor**: Risk + Cycle Enforcement  

---

## Quick Start

### 1. Environment Setup
```powershell
# Set Google Cloud credentials
$env:GOOGLE_APPLICATION_CREDENTIALS="path\to\serviceAccountKey.json"
```

### 2. Install Dependencies
```powershell
# Backend
cd nexus-core
pip install -r requirements.txt

# Frontend
cd ..\nexus-terminal
npm install
```

### 3. Launch System
```powershell
# From nexus-genesis root
.\dev.ps1
```

This starts:
- **Nexus Core** (FastAPI) on `http://localhost:8080`
- **Nexus Terminal** (Vite) on `http://localhost:5173`

---

## Testing

### Brain Test
```powershell
cd nexus-core
python test_brain.py
```

### Stress Test (Risk Governor)
```powershell
cd nexus-core
python stress_test.py
```

---

## Deployment

### Google Cloud Run
```powershell
gcloud config set project nexus-dyron-777
gcloud builds submit --config cloudbuild.yaml .
```

---

## Architecture

- **Vault**: Secure secrets via Google Secret Manager
- **Intelligence**: Market analysis via Vertex AI (Claude)
- **Execution**: Trade execution via CCXT/MT5
- **Risk Governor**: 2% max drawdown, 5% position size, 3x ATR anomaly detection
- **Ancient Logic**: Cycle-based signal filtering
- **Scheduler**: Autonomous 15-minute heartbeat

---

## Security Directives

- Zero Trust: All secrets in Secret Manager
- No public cloud AI trading without Governor approval
- Backend supremacy: Frontend is display only
