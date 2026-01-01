# NEXUS Security Model

## Overview

NEXUS implements defense-in-depth security following the principle of least privilege. This document outlines the security architecture, controls, and procedures.

---

## Secret Management

### Policy: Zero Secrets in Code

**Prohibited:**
- API keys in source code
- Secrets in environment files committed to git
- Credentials in frontend code
- Hardcoded passwords anywhere

**Required:**
- All secrets stored in Google Secret Manager
- Secrets accessed via IAM service account
- Secret rotation supported via versioning

### Secret Inventory

| Secret ID | Description | Rotation |
|-----------|-------------|----------|
| `BINANCE_API_KEY` | Binance API key | 90 days |
| `BINANCE_API_SECRET` | Binance API secret | 90 days |
| `MT5_LOGIN` | MetaTrader account number | As needed |
| `MT5_PASSWORD` | MetaTrader password | 90 days |
| `MT5_SERVER` | Broker server address | Static |
| `POLYGON_API_KEY` | Market data API key | 90 days |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase admin SDK | Annual |

### Accessing Secrets

```python
from app.services.vault import get_secret

# Secrets fetched at runtime, never stored in variables long-term
api_key = get_secret("BINANCE_API_KEY")
```

---

## IAM Configuration

### Service Account: `nexus-runtime@nexus-dyron-777.iam.gserviceaccount.com`

```yaml
roles:
  # Secret Manager access
  - roles/secretmanager.secretAccessor
  
  # Vertex AI model invocation
  - roles/aiplatform.user
  
  # Firestore for state persistence
  - roles/datastore.user
  
  # Cloud Logging
  - roles/logging.logWriter
```

### Principle of Least Privilege

- Service account has **no** admin permissions
- Cannot create/delete secrets, only read
- Cannot modify IAM policies
- Cannot access other projects

---

## Network Security

### Cloud Run Configuration

```yaml
# Production settings
ingress: internal          # Only internal traffic
authentication: required   # All requests authenticated
vpc-connector: enabled     # Private VPC access
```

### Firewall Rules

- No public endpoints in production
- Frontend accesses backend via Cloud Run invoker role
- All external API calls over HTTPS

---

## Authentication & Authorization

### Backend Authentication

- Cloud Run requires IAM authentication
- No anonymous access in production
- Service-to-service auth via OIDC tokens

### Frontend Authentication

- Firebase Admin SDK authentication
- Admin users managed via Firebase Console
- No public registration
- Session tokens with 1-hour expiry

---

## Audit Logging

### What We Log

| Event | Log Level | Details |
|-------|-----------|---------|
| Trade execution | INFO | Symbol, side, quantity, result |
| Risk rejection | WARNING | Reason, parameters |
| Kill switch | CRITICAL | Trigger source, timestamp |
| Secret access | INFO | Secret ID (not value) |
| Circuit breaker | WARNING | State changes |
| Authentication | INFO | User, result |

### Log Retention

- Cloud Logging: 30 days default
- Critical events: 365 days
- Exported to BigQuery for analysis

### Viewing Logs

```powershell
# Recent critical events
gcloud logging read "severity>=WARNING" \
    --project=nexus-dyron-777 \
    --limit=50

# Specific module
gcloud logging read 'jsonPayload.name="nexus.execution"' \
    --project=nexus-dyron-777
```

---

## Incident Response

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| P1 | Trading system compromised | Immediate |
| P2 | Circuit breaker triggered | 15 minutes |
| P3 | API errors/degradation | 1 hour |
| P4 | Monitoring alert | 24 hours |

### Response Procedures

**P1 - Immediate Actions:**
1. Trigger kill switch: `POST /kill`
2. Revoke all API keys (Binance, MT5)
3. Rotate Secret Manager secrets
4. Analyze audit logs
5. Engage incident response team

**P2 - Circuit Breaker:**
1. Review trigger cause
2. Analyze market conditions
3. Wait for cooldown or manual reset
4. Resume with reduced exposure

---

## Vulnerability Management

### Dependencies

- Automated scanning via `safety` and `pip-audit`
- Weekly dependency updates reviewed
- Critical CVEs patched within 24 hours

### Code Security

- No `eval()` or dynamic code execution
- Input validation on all endpoints
- SQL injection not applicable (no SQL)
- XSS not applicable (API only)

---

## Secrets Rotation Procedure

### Binance API Keys

1. Generate new API key in Binance console
2. Add new version to Secret Manager:
   ```powershell
   echo -n "NEW_KEY" | gcloud secrets versions add BINANCE_API_KEY --data-file=-
   ```
3. Deploy new Cloud Run revision
4. Verify trading works with new key
5. Disable old key in Binance console

### MT5 Credentials

1. Change password in broker portal
2. Update Secret Manager
3. Restart MT5 bridge connection
4. Verify connection

---

## Compliance Checklist

- [ ] All secrets in Secret Manager
- [ ] Service account has minimal permissions
- [ ] Cloud Run requires authentication
- [ ] Audit logging enabled
- [ ] No secrets in git repository
- [ ] API keys rotated every 90 days
- [ ] Incident response plan documented
- [ ] Backup and recovery tested

---

## Contact

Security issues: Report immediately to system administrator.
