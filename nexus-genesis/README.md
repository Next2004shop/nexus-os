# NEXUS SOVEREIGN SYSTEM v3.0

> **A system that cannot survive destruction does not deserve profit.**

## System Overview

NEXUS is a **crash-immune, multi-agent private trading intelligence system** that:

- Runs **permanently** on Google Cloud
- Makes decisions via **5-agent council** (3/5 quorum required)
- Executes trades via **MetaTrader 5** on secure VM
- Auto-deploys on every Git push
- Has a **Master AI** that responds to your commands
- **Never exposes API keys to frontend**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (READ-ONLY)                          │
│                     No API keys, No credentials                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        GOOGLE CLOUD RUN                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    NEXUS CORE (FastAPI)                          │   │
│  │                                                                   │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │              MULTI-AGENT COUNCIL (5 Agents)              │   │   │
│  │  │  MarketStructure │ Momentum │ VolRisk │ Macro │ Safety  │   │   │
│  │  │                   QUORUM: 3/5 REQUIRED                   │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  │                              │                                   │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │              MODEL ENSEMBLE (3 Models)                   │   │   │
│  │  │        GeminiPro │ RuleBased │ PatternMatcher            │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  │                              │                                   │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │              MASTER AI COMMAND CORE                      │   │   │
│  │  │     "status" "pause" "resume" "explain trade" "kill"     │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  │                              │                                   │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │              STEALTH MODE                                │   │   │
│  │  │   Encrypted Logs │ Response Minimizer │ Self-Purge       │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  SECRET MANAGER │      │   GOOGLE VM     │      │    BINANCE      │
│  (Credentials)  │      │  (MT5 Bridge)   │      │   (Crypto)      │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

---

## Immutable Laws

| # | Law | Enforcement |
|---|-----|-------------|
| 1 | **NO API KEYS ON FRONTEND** | Backend-only connectors, Secret Manager |
| 2 | **Council Over King** | 5 agents vote, 3/5 quorum required |
| 3 | **Silence Is Security** | Encrypted logs, minimal responses |
| 4 | **Preservation > Profit** | 2% max drawdown, Safety Agent veto |
| 5 | **Failure Is Assumed** | Auto-heal, auto-restart, self-purge |
| 6 | **Only One Master** | You control everything |

---

## Quick Start

### 1. Prerequisites

```bash
# Google Cloud CLI
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com
```

### 2. Store Secrets

```bash
# Store trading credentials in Secret Manager
echo -n "YOUR_BINANCE_API_KEY" | gcloud secrets create BINANCE_API_KEY --data-file=-
echo -n "YOUR_BINANCE_SECRET" | gcloud secrets create BINANCE_API_SECRET --data-file=-
echo -n "YOUR_MT5_LOGIN" | gcloud secrets create MT5_LOGIN --data-file=-
echo -n "YOUR_MT5_PASSWORD" | gcloud secrets create MT5_PASSWORD --data-file=-
echo -n "YOUR_MT5_SERVER" | gcloud secrets create MT5_SERVER --data-file=-
echo -n "YOUR_USER_ID" | gcloud secrets create NEXUS_MASTER_USER_ID --data-file=-
```

### 3. Deploy

```bash
cd nexus-genesis/nexus-core
gcloud builds submit --config cloudbuild.yaml .
```

### 4. Verify

```bash
SERVICE_URL=$(gcloud run services describe nexus-core --region us-central1 --format 'value(status.url)')
TOKEN=$(gcloud auth print-identity-token)

# Health check
curl -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/health"

# System status
curl -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/status"
```

---

## Master AI Commands

Talk to NEXUS via the `/ai/command` endpoint:

| Command | Action |
|---------|--------|
| `status` | Full system status report |
| `pause` | Halt all trading |
| `resume` | Resume trading |
| `explain trade` | Explain last trade decision |
| `risk` | Risk summary |
| `stealth` | Enable stealth mode |
| `kill` | Emergency shutdown |
| `buy EURUSD` | Execute buy order |
| `sell BTCUSD` | Execute sell order |
| `close all` | Close all positions |

**Example:**
```bash
curl -X POST "$SERVICE_URL/ai/command" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "status"}'
```

---

## API Endpoints

### Health & Status
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/status` | GET | Full system status |
| `/risk-status` | GET | Risk metrics |

### Trading
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/trade` | POST | Execute trade (requires council quorum) |
| `/kill` | POST | Emergency kill switch |
| `/resume` | POST | Resume after halt |

### Master AI
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ai/command` | POST | Send command to Master AI |
| `/ai/status` | GET | Master AI status |

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Login with Firebase token |
| `/auth/logout` | POST | Logout session |
| `/auth/session` | GET | Get session info |

### Trading Accounts
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/accounts/register` | POST | Register trading account |
| `/accounts/list` | GET | List accounts (safe info) |

### Live Data
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/data/tick/{symbol}` | GET | Get live tick |
| `/data/health` | GET | Data integrity check |

---

## Trade Execution Flow

```
1. Stealth Mode Check     → System operational?
2. Agent Council          → 3/5 quorum required
3. Model Ensemble         → AI + Rule-based consensus
4. Ancient Logic          → Cycle alignment
5. Risk Governor          → Drawdown & position limits
6. Circuit Breaker        → API & price stability
7. MT Bridge Execution    → Signed trade instruction
```

A trade is **REJECTED** if any step fails.

---

## File Structure

```
nexus-genesis/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitOps CI/CD
├── nexus-core/
│   ├── app/
│   │   ├── main.py             # FastAPI application
│   │   └── services/
│   │       ├── agent_council.py    # 5-agent voting council
│   │       ├── model_ensemble.py   # AI model voting
│   │       ├── master_ai.py        # Command interface
│   │       ├── auth_service.py     # Authentication
│   │       ├── live_data.py        # Real-time data
│   │       ├── mt_bridge.py        # MetaTrader bridge
│   │       ├── stealth_mode.py     # Security features
│   │       ├── risk_governor.py    # Risk management
│   │       └── circuit_breaker.py  # Failure protection
│   ├── tests/
│   ├── cloudbuild.yaml         # Deployment config
│   ├── Dockerfile
│   └── requirements.txt
├── infrastructure/
│   └── vm_startup.ps1          # VM auto-start script
└── README.md
```

---

## Emergency Procedures

### Kill Switch
```bash
curl -X POST "$SERVICE_URL/kill" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol": null, "purge": false}'
```

### Resume After Halt
```bash
curl -X POST "$SERVICE_URL/resume" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"admin_key": "YOUR_ADMIN_KEY"}'
```

### Rollback Deployment
```bash
# Via GitHub Actions
gh workflow run deploy.yml -f force_deploy=rollback

# Or manually
gcloud run services update-traffic nexus-core \
  --region us-central1 \
  --to-revisions PREVIOUS_REVISION=100
```

---

## Security Model

1. **Zero Secrets in Code** - All credentials in Secret Manager
2. **Backend-Only Data** - Frontend only receives safe data
3. **Encrypted Credentials** - Trading passwords encrypted at rest
4. **Session Tokens** - Short-lived, invalidated on suspicious activity
5. **Signed Trade Instructions** - HMAC-signed messages to MT bridge
6. **Anomaly Detection** - Rate limiting and access pattern monitoring
7. **Self-Purge** - Emergency data destruction capability

---

## Status

| Component | Status |
|-----------|--------|
| Multi-Agent Council | ✅ Implemented |
| Model Ensemble | ✅ Implemented |
| Master AI | ✅ Implemented |
| Authentication | ✅ Implemented |
| Live Data | ✅ Implemented |
| MT Bridge | ✅ Implemented |
| GitOps Pipeline | ✅ Implemented |
| VM Auto-Start | ✅ Implemented |
| Stealth Mode | ✅ Implemented |
| Self-Healing | ✅ Implemented |

---

## Support

This is a private system. All issues should be resolved via the Master AI:

```bash
curl -X POST "$SERVICE_URL/ai/command" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"command": "help"}'
```

---

> **"Live data without control is chaos. Control without secrecy is death. Nexus survives by silence, redundancy, and discipline."**
