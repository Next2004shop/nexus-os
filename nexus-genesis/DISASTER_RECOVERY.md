# NEXUS Disaster Recovery

## Overview

This document outlines procedures for recovering the NEXUS trading system from various failure scenarios. The goal is to minimize capital exposure and restore normal operations safely.

---

## Emergency Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| System Admin | Primary operator | Immediate |
| Broker Support | MT5 broker hotline | Account issues |
| GCP Support | Google Cloud console | Infrastructure |

---

## Quick Reference

### Immediate Kill Switch

```powershell
# Via API
curl -X POST https://nexus-core-xxxxx.run.app/kill \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"

# Via gcloud (scale to zero)
gcloud run services update nexus-core --min-instances=0 --max-instances=0
```

### Check System Status

```powershell
curl https://nexus-core-xxxxx.run.app/status \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

---

## Failure Scenarios

### 1. Excessive Drawdown (>2%)

**Symptoms:**
- Risk governor disables trading
- `/risk-status` shows `SHUTDOWN` state

**Recovery:**
1. Review drawdown cause in Cloud Logging
2. Verify no open positions (close manually if needed)
3. Assess if drawdown was legitimate or system error
4. If legitimate: Reduce initial equity or increase limit
5. Reset governor state in Firestore:
   ```javascript
   // In Firestore Console
   // Collection: nexus_risk_state
   // Document: global_state
   {
     "trading_enabled": true,
     "current_equity": 9800,  // Actual current value
     "peak_equity": 9800,     // Reset peak to current
     "risk_level": "NORMAL"
   }
   ```
6. Resume trading: `POST /resume` with admin key

---

### 2. Circuit Breaker Triggered

**Symptoms:**
- Trades rejected with "CIRCUIT_BREAKER_ACTIVE"
- `/status` shows open circuit breakers

**Recovery:**
1. Wait for automatic timeout (60 seconds default)
2. Or manually reset via API:
   ```powershell
   curl -X POST https://nexus-core-xxxxx.run.app/resume \
     -H "Content-Type: application/json" \
     -d '{"admin_key": "your-admin-key"}'
   ```
3. Monitor for recurring failures

---

### 3. API Connectivity Lost

**Symptoms:**
- Binance orders failing
- MT5 disconnected
- Polygon data stale

**Recovery (Binance):**
1. Check Binance status: https://www.binance.com/en/support
2. Verify API key not expired/revoked
3. Check IP whitelist if enabled
4. Rotate API key if compromised

**Recovery (MT5):**
1. Check broker server status
2. Verify account not locked
3. Restart MT5 terminal on bridge server
4. Re-authenticate with credentials

**Recovery (Polygon):**
1. Check Polygon status: https://status.polygon.io
2. Verify API key quota not exceeded
3. System will use cached data during outage

---

### 4. Cloud Run Service Down

**Symptoms:**
- 503 errors from Cloud Run
- Scheduler heartbeat not firing

**Recovery:**
1. Check Cloud Run console for errors
2. Review recent deployments for issues
3. Rollback to previous revision:
   ```powershell
   gcloud run services update-traffic nexus-core \
     --to-revisions=nexus-core-00005-abc=100
   ```
4. If persistent, redeploy:
   ```powershell
   gcloud builds submit --config cloudbuild.yaml .
   ```

---

### 5. Secret Manager Access Denied

**Symptoms:**
- "Permission denied" errors in logs
- Service fails to start

**Recovery:**
1. Verify service account exists:
   ```powershell
   gcloud iam service-accounts describe \
     nexus-runtime@nexus-dyron-777.iam.gserviceaccount.com
   ```
2. Re-grant permissions:
   ```powershell
   gcloud projects add-iam-policy-binding nexus-dyron-777 \
     --member="serviceAccount:nexus-runtime@nexus-dyron-777.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```
3. Redeploy service

---

### 6. Firestore State Corruption

**Symptoms:**
- Inconsistent risk state
- Positions not tracking correctly

**Recovery:**
1. Export current state for analysis
2. Reset to known good state:
   ```javascript
   // Firestore Console - nexus_risk_state/global_state
   {
     "peak_equity": 10000.0,
     "current_equity": 10000.0,
     "initial_equity": 10000.0,
     "max_drawdown_limit": 0.02,
     "warning_drawdown": 0.01,
     "max_position_size_pct": 0.05,
     "max_total_exposure_pct": 0.20,
     "trading_enabled": false,  // Start disabled
     "circuit_breaker_active": false,
     "risk_level": "NORMAL",
     "consecutive_losses": 0,
     "open_positions": {}
   }
   ```
3. Manually reconcile open positions
4. Re-enable trading after verification

---

## Position Reconciliation

If system state diverges from actual positions:

### 1. Get Actual Positions

**Binance:**
```python
import ccxt
exchange = ccxt.binance({...})
positions = exchange.fetch_balance()
print(positions)
```

**MT5:**
```python
import MetaTrader5 as mt5
mt5.initialize()
positions = mt5.positions_get()
for pos in positions:
    print(pos)
```

### 2. Update System State

```python
from app.services import risk_governor

# Clear system state
state = risk_governor._get_state()
state.open_positions = {}

# Add actual positions
risk_governor.register_position("EURUSD", 0.1, 1.0850, "BUY")
risk_governor.register_position("BTCUSD", 0.01, 42000, "SELL")

# Update equity
risk_governor.update_equity(actual_equity)
```

---

## Backup Procedures

### Firestore Export

```powershell
gcloud firestore export gs://nexus-backups/$(Get-Date -Format "yyyy-MM-dd")
```

### Cloud Run Configuration

```powershell
gcloud run services describe nexus-core --format=yaml > nexus-core-config.yaml
```

---

## Post-Incident Review

After any P1/P2 incident:

1. **Timeline**: Document when issue was detected, diagnosed, resolved
2. **Root Cause**: Identify underlying cause
3. **Impact**: Quantify any losses or missed opportunities
4. **Prevention**: What changes prevent recurrence?
5. **Detection**: How can we detect faster next time?

Document in incident log and update runbooks.

---

## Testing Recovery Procedures

**Monthly:**
- Test kill switch activation
- Verify Firestore state reset
- Practice rollback procedure

**Quarterly:**
- Full disaster recovery drill
- Verify backup restoration
- Test with paper trading

---

## Runbook Checklist

- [ ] Kill switch tested and working
- [ ] Admin key securely stored
- [ ] Broker emergency contacts available
- [ ] Cloud console access verified
- [ ] Recent Firestore backup exists
- [ ] Rollback revision identified
