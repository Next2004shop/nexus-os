# NEXUS System Execution Map
## CPP-1 Audit — System Lifecycle Analysis

**Prepared by:** System Performance Architect
**Audit Date:** 2026-02-22
**Codebase:** nexus-genesis/nexus-core (FastAPI, Python 3.x)

---

## 1. System Overview

Nexus is an institutional-grade algorithmic trading platform built on FastAPI (Python). It targets Forex (MetaTrader 5 via VM bridge), Crypto (Binance REST/WebSocket), and Stocks (Polygon.io). The system runs as a single Python process on Google Cloud Run.

**Infrastructure topology:**
- **Backend process:** FastAPI + Uvicorn on Cloud Run (Linux, Python)
- **MT5 bridge:** Separate Windows VM on Google Cloud — Nexus communicates with it over HTTP
- **Firestore:** Risk state persistence (Google Cloud Firestore)
- **Vertex AI:** Gemini Pro LLM calls for market regime analysis
- **Frontend:** React/TypeScript terminal (nexus-terminal), WebSocket consumer

---

## 2. Startup Sequence

File: `app/main.py` — `startup_event()` (line 243)

```
1. validate_environment()           — env var gate
2. scheduler.start_scheduler()      — APScheduler, 15-min heartbeat armed
3. seed_admin()                     — Firebase admin user init
4. circuit_breaker.get_manager()    — Hystrix-style breaker init
5. get_council()                    — AgentCouncil (5 agents instantiated)
6. get_ensemble()                   — ModelEnsemble (3 models instantiated)
7. get_stealth_mode()               — Stealth mode controller
8. initialize_live_data()           — Binance WebSocket + MT bridge connector started
   └── BinanceConnector.connect()   — wss://stream.binance.com:9443/ws
   └── MetaTraderConnector.connect()— HTTP health check to localhost:5000 (MT bridge VM)
   └── PolygonConnector (optional)  — wss://socket.polygon.io/stocks (if key available)
9. asyncio.create_task(status_broadcaster()) — every-2s WS broadcaster started
10. telegram.start()                — Telegram bot listener started
11. get_telemetry().start()         — TelemetryEngine started
12. get_guard().start()             — RuntimeGuard started
13. get_strategy_engine()           — StrategyEngine singleton
14. strat_engine.load_strategy(BreakoutStrategy()) — default strategy loaded
15. strat_engine.start()            — 1Hz _process_loop asyncio task started
```

**Total background tasks spawned at startup:** ≥5 asyncio tasks running continuously.

---

## 3. Persistent Background Loops

These run for the lifetime of the process.

### 3.1 Strategy Engine Loop — 1 Hz
**File:** `strategies/strategy_engine.py:70-110`

```
while self._running:
    for each loaded strategy:
        signals = await strategy.analyze(self.market_provider)  # Polygon REST + indicator math
        for signal in signals:
            await _route_signal(signal)                          # → command/router.py
    await asyncio.sleep(1)                                       # 1-second cadence
```

Per tick per strategy:
- `provider.get_ohlcv()` → Polygon REST (or 5-min cache)
- Rolling Bollinger Bands, RSI/ROC in pandas over 50 bars
- Signal routing through full command pipeline if signal fires

### 3.2 15-Minute Scheduler (APScheduler)
**File:** `app/services/scheduler.py:9-83`

```
Every 15 minutes (aligned to M15 candle boundary):
    1. engine.mt5._mt5.account_info()   — synchronous MT5 call (Windows SDK)
    2. intelligence.analyze_market()    — Vertex AI Gemini Pro HTTP call (~500ms–2s)
    3. ancient_logic.check_cycle()      — dict lookup (negligible)
    4. risk_governor.validate_trade()   — Firestore read + state computation
    5. engine.execute_trade()           — MT5 or Binance order placement
```

### 3.3 MT Bridge Quote Poller — 2 Hz
**File:** `app/services/live_data.py:428-450`

```
while self._running:
    GET {bridge_url}/quotes           — HTTP request to MT5 VM
    for q in quotes:
        LiveTick(...)                 — object construction
        await _notify_callbacks(tick) — WS broadcast chain
    await asyncio.sleep(0.5)          — 500ms cadence
```

### 3.4 Binance WebSocket Message Handler — Market-Driven
**File:** `app/services/live_data.py:189-216`

```
while self._running:
    msg = await ws.recv()             — awaits Binance server push
    parse JSON                        — json.loads()
    LiveTick(...)                     — object construction
    await _notify_callbacks(tick)     — WS broadcast chain
```

Frequency: driven by Binance tick volume — potentially 10–50 messages/sec on active symbols.

### 3.5 System Status Broadcaster — 0.5 Hz
**File:** `app/main.py:349-358`

```
Every 2 seconds:
    await system_status()            — queries 6 subsystems
    await ws_hub.broadcast_status()  — JSON serialize + send to all WS clients
```

---

## 4. Trade Execution Pipeline (On-Demand)

Triggered by: `POST /trade` endpoint or `_route_signal()` from Strategy Engine.

```
POST /trade
│
├── GATE 0: RateLimiter.check()                  [main.py:163-181]
│     token bucket list scan, O(k) per request
│
├── GATE 1: AuthMiddleware + require_trader()     [auth/middleware.py]
│     session token validation
│
├── GATE 2: stealth_mode.is_operational()         [services/stealth_mode.py]
│     system state flag check
│     optional: asyncio.sleep(delay)              ← stealth delay injection
│
├── GATE 3: AgentCouncil.deliberate()             [services/agent_council.py:739-774]
│     5 agents analyze in series (Python for-loop, NOT parallel):
│     ├── MarketStructureAgent.analyze()          — Wyckoff: np.max/min, rolling means (50 bars)
│     ├── MomentumAgent.analyze()                 — ROC + RSI: np.diff, np.mean (14-period)
│     ├── VolatilityRiskAgent.analyze()           — ATR percentile: O(n²) Python loop ⚠ HOTSPOT
│     ├── MacroSentimentAgent.analyze()           — MA50/MA200: np.mean (200-bar lookback)
│     └── ExecutionSafetyAgent.analyze()          — spread check, circuit breaker status
│     _calculate_consensus() → weighted vote aggregation
│     QUORUM REQUIRED: 3/5 agents + weighted threshold ≥ 60%
│     Returns: CouncilDecision (position_size_modifier)
│
├── GATE 4: ModelEnsemble.predict()               [services/model_ensemble.py:423-457]
│     3 models run in series (Python for-loop, NOT parallel):
│     ├── GeminiModel.predict()                   — Vertex AI HTTP call ⚠ LATENCY 500ms–2s
│     ├── RuleBasedModel.predict()                — pure Python scoring rules
│     └── PatternModel.predict()                  — sequential similarity scan ⚠ HOTSPOT
│     _aggregate_predictions() → weighted vote
│     Returns: EnsembleDecision (should_halt, position_modifier)
│
├── GATE 5: ancient_logic.check_cycle()           [services/ancient_logic.py:38-72]
│     dict lookup — O(1)
│
├── GATE 6: risk_governor.validate_trade()        [services/risk_governor.py:268-358]
│     _get_state() → Firestore read (or in-memory cache) ⚠ NETWORK
│     calculate_drawdown()       — float arithmetic
│     position size check        — float arithmetic
│     exposure check             — sum() over open_positions dict
│     ATR anomaly check          — float comparison
│     _save_state()              → Firestore write ⚠ NETWORK
│
├── GATE 7: circuit_breaker.is_trading_allowed()  [services/circuit_breaker.py:426-436]
│     iterates _breakers dict — O(n) breakers
│
└── GATE 8: ExecutionEngine.execute_trade()       [services/execution.py:582-769]
      mt5.get_current_price()                     — MT5 SDK call (sync)
      ExecutionOptimizer.optimize_entry()         — async from sync via run_coroutine_threadsafe ⚠
        └── market_provider.get_ohlcv()           — Polygon REST + EMA calculation
      MT5Executor.execute()                       — self._mt5.order_send() (sync Windows SDK)
        OR BinanceExecutor.execute()              — CCXT REST call (sync)
      risk_governor.register_position()           — Firestore write
```

**Total pipeline depth:** 8 gates, 5 agent analyses, 3 model predictions, 2+ network calls (Vertex AI, Firestore, MT5/Binance).

---

## 5. Command Routing Path (from Strategy Engine)

```
StrategyEngine._route_signal(signal)              [strategy_engine.py:112-137]
    → route_command(TradeCommand)                 [command/router.py]
        → capital_allocator.allocate()            [risk/capital_allocator.py]
        → validator.validate()                    [command/validator.py]
        → execution.get_engine().execute_trade()  [services/execution.py]
```

This path does NOT go through the Agent Council or Model Ensemble — signals from StrategyEngine bypass the AI voting pipeline and route directly to execution with capital allocator sizing.

---

## 6. Data Flow Architecture

```
External Feeds
│
├── Binance WebSocket ──────────────────┐
│   (market-driven, async)              │
│                                       ▼
├── MetaTrader Bridge REST poll (2Hz) → LiveDataManager.ticks{}
│   (sync GET, 500ms interval)          │
│                                       │
└── Polygon.io REST (on-demand)         ├── callbacks → WebSocket broadcast
    (5-min cache, async)                │

Strategy Engine (1Hz)                   │
    └── get_ohlcv() ─────────────────── ┤ (separate read path, cached)
                                        │
/trade endpoint                         │
    └── market_context from caller ─────┘ (caller must supply OHLCV context)

Risk Governor                          ↔ Firestore (Cloud Firestore)
Intelligence                           ↔ Vertex AI (Google Cloud)
Telegram                               ↔ Telegram API
```

---

## 7. WebSocket Event Loop

**File:** `app/main.py:390-417`

```
/ws/nexus endpoint:
while connected:
    data = await websocket.receive_text()
    message = json.loads(data)

    if SUBSCRIBE: subscribe to symbol list
    if PING: send PONG

Incoming broadcasts (pushed to client):
    - Tick data: from LiveDataManager callbacks (Binance/MT5 rate)
    - Status: from status_broadcaster (every 2s)
```

---

## 8. Observed Runtime Concurrency Model

The system runs on a single Python asyncio event loop. All background tasks share this loop via `asyncio.create_task()`. The GIL is the primary concurrency constraint for CPU-bound operations.

**Notable concurrency hazard:**
`ExecutionEngine.execute_trade()` is a synchronous function called from both async route handlers and the async Strategy Engine. It internally calls `asyncio.run_coroutine_threadsafe(...).result()` to run the async `optimize_entry()`. This pattern can deadlock if the calling asyncio loop is blocked.

**Sync code in async context:**
- `risk_governor._get_state()` and `_save_state()` — synchronous Firestore calls
- `vault.get_secret()` — synchronous Google Secret Manager calls
- `MT5Executor._execute_internal()` — synchronous Windows SDK calls (platform-native)

---

## 9. Module Dependency Graph (Simplified)

```
main.py
├── scheduler.py
│   ├── intelligence.py → vertexai
│   ├── ancient_logic.py
│   ├── risk_governor.py → firestore
│   └── execution.py → mt5 / binance
│
├── /trade route
│   ├── agent_council.py → numpy, pandas
│   ├── model_ensemble.py → vertexai (GeminiModel), numpy
│   ├── ancient_logic.py
│   ├── risk_governor.py → firestore
│   └── execution.py
│       ├── execution_optimizer.py → market_data.py → polygon.io
│       ├── mt_bridge.py → aiohttp → MT5 VM
│       └── ccxt → Binance
│
└── strategy_engine.py (1Hz loop)
    ├── market_data.py → polygon.io
    ├── breakout.py / mean_reversion.py → pandas
    └── command/router.py → execution.py
```

---

## 10. Technology Stack Summary

| Layer | Technology |
|---|---|
| Web framework | FastAPI + Uvicorn |
| Async I/O | Python asyncio |
| Numerical computation | NumPy, pandas |
| AI inference | Vertex AI (Gemini 1.5 Pro), Claude 3.5 Haiku (backup) |
| Market data | Polygon.io REST, Binance WebSocket, MT5 bridge REST |
| State persistence | Google Cloud Firestore |
| Secrets | Google Cloud Secret Manager |
| Scheduling | APScheduler (AsyncIOScheduler) |
| Primary execution | MetaTrader 5 (Windows SDK via VM) |
| Secondary execution | Binance via CCXT |
| Frontend | React/TypeScript + Vite (nexus-terminal) |
| Monitoring | Custom telemetry engine, Google Cloud Logging |
