"""
NEXUS Performance Intelligence - Autonomous Adaptive Meta-Layer
================================================================

Phase 10: Continuous performance evaluation and safe parameter adjustment.

STRICT CONSTRAINTS:
- Does NOT modify existing strategy logic.
- Does NOT modify RiskGovernor rules.
- Does NOT modify ExecutionOptimizer mechanics.
- Only adjusts WEIGHTS and PARAMETERS within bounded ranges.
- All changes are reversible, logged, and rate-limited.
- No random ML. No uncontrolled self-rewriting. Only parameter adaptation.

Subsystems:
    A) Trade Journal Engine        - Records every closed trade
    B) Performance Analyzer        - Computes rolling statistics
    C) Regime Classifier           - Classifies current market regime
    D) Strategy Weighting          - Adjusts strategy allocation weights
    E) Risk Dynamic Modulation     - Temporary risk % adjustments
    F) Self-Health Check           - Execution quality monitoring
    G) Adaptation Safety           - Rate-limiting and reversal guarantees
    H) Performance Dashboard       - Telemetry panel data
    I) Daily Review Summary        - End-of-day meta report
    J) Hard Safety (PROTECTIVE MODE)
"""

import asyncio
import json
import logging
import os
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.meta_intelligence")


# =============================================================================
# CONSTANTS & PATHS
# =============================================================================

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_BASE_DIR, "data")
STATE_DIR = os.path.join(_BASE_DIR, "state")
LOGS_DIR = os.path.join(_BASE_DIR, "logs")

LEDGER_PATH = os.path.join(DATA_DIR, "performance_ledger.json")
REGIME_PATH = os.path.join(STATE_DIR, "market_regime.json")
ADAPTATION_LOG_PATH = os.path.join(LOGS_DIR, "adaptation.log")
DAILY_REPORT_DIR = os.path.join(DATA_DIR, "daily_reports")

# Ensure directories exist
for d in [DATA_DIR, STATE_DIR, LOGS_DIR, DAILY_REPORT_DIR]:
    os.makedirs(d, exist_ok=True)

# Adaptation constraints
WEIGHT_MAX_MULTIPLIER = 1.3      # No weight > 1.3x baseline
WEIGHT_MIN_MULTIPLIER = 0.7      # No weight < 0.7x baseline
WEIGHT_STEP = 0.02               # Max change per adjustment cycle
RISK_MODULATION_STEP = 0.05      # Max risk change per cycle (5%)
RISK_MODULATION_MIN = 0.5        # Floor: 50% of base risk
RISK_MODULATION_MAX = 1.15       # Ceiling: 115% of base risk
ADAPTATION_COOLDOWN_SECONDS = 300  # 5 minutes between adaptations
ANALYSIS_TRADE_WINDOW = 20       # Analyze every N trades
PROTECTIVE_MODE_THRESHOLD = 0.4  # Rolling 30-trade win rate threshold
HEALTH_CHECK_WINDOW = 10         # Last N trades for health scoring


# =============================================================================
# ENUMS
# =============================================================================

class MarketRegime(str, Enum):
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    NEWS_DRIVEN = "NEWS_DRIVEN"
    UNKNOWN = "UNKNOWN"


class AdaptationMode(str, Enum):
    NORMAL = "NORMAL"
    CAUTIOUS = "CAUTIOUS"         # Drawdown rising
    AGGRESSIVE = "AGGRESSIVE"     # Strong streak
    PROTECTIVE = "PROTECTIVE"     # Hard safety triggered
    REDUCED_ACTIVITY = "REDUCED_ACTIVITY"  # Health check triggered


# =============================================================================
# A) TRADE JOURNAL ENGINE
# =============================================================================

@dataclass
class TradeRecord:
    """Single closed trade record for the performance ledger."""
    trade_id: str
    timestamp: str
    strategy_used: str
    asset: str
    lot_size: float
    entry_price: float
    exit_price: float
    r_multiple: float
    slippage: float
    execution_score: float       # 0.0–1.0
    time_of_day: str             # HH:MM UTC
    volatility_regime: str
    macro_state: str
    win_or_loss: str             # "WIN" or "LOSS"
    pnl: float
    holding_duration_seconds: float = 0.0


class TradeJournal:
    """
    Persistent trade journal — every closed trade is recorded to disk.
    Storage: /data/performance_ledger.json
    """

    def __init__(self, ledger_path: str = LEDGER_PATH):
        self._path = ledger_path
        self._records: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        """Load existing ledger from disk."""
        if os.path.exists(self._path):
            try:
                with open(self._path, "r") as f:
                    data = json.load(f)
                self._records = data.get("trades", [])
                logger.info(f"Loaded {len(self._records)} trade records from ledger")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load ledger: {e}. Starting fresh.")
                self._records = []
        else:
            self._records = []

    def _save(self):
        """Persist ledger to disk."""
        try:
            payload = {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_trades": len(self._records),
                "trades": self._records
            }
            with open(self._path, "w") as f:
                json.dump(payload, f, indent=2, default=str)
        except IOError as e:
            logger.error(f"Failed to save ledger: {e}")

    def record_trade(self, trade: TradeRecord):
        """Record a closed trade."""
        self._records.append(asdict(trade))
        self._save()
        logger.info(
            f"Trade recorded: {trade.asset} | {trade.strategy_used} | "
            f"{trade.win_or_loss} | R={trade.r_multiple:.2f}"
        )

    def get_recent(self, count: int = 30) -> List[Dict[str, Any]]:
        """Get most recent N trades."""
        return self._records[-count:]

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all trade records."""
        return list(self._records)

    def get_by_strategy(self, strategy: str, count: int = 50) -> List[Dict[str, Any]]:
        """Get trades for a specific strategy."""
        filtered = [t for t in self._records if t.get("strategy_used") == strategy]
        return filtered[-count:]

    def get_by_regime(self, regime: str, count: int = 50) -> List[Dict[str, Any]]:
        """Get trades from a specific market regime."""
        filtered = [t for t in self._records if t.get("volatility_regime") == regime]
        return filtered[-count:]

    @property
    def total_trades(self) -> int:
        return len(self._records)


# =============================================================================
# B) PERFORMANCE ANALYZER
# =============================================================================

@dataclass
class PerformanceSnapshot:
    """Performance statistics over a trade window."""
    window_size: int = 0
    win_rate: float = 0.0
    avg_r_multiple: float = 0.0
    avg_slippage: float = 0.0
    drawdown_depth: float = 0.0
    profit_factor: float = 0.0
    total_pnl: float = 0.0
    best_r: float = 0.0
    worst_r: float = 0.0
    avg_execution_score: float = 0.0
    regime_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)
    strategy_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)


class PerformanceAnalyzer:
    """
    Analyzes rolling trade performance every N trades.
    Computes win rate, R-multiples, drawdown, profit factor, regime breakdown.
    """

    def analyze(self, trades: List[Dict[str, Any]]) -> PerformanceSnapshot:
        """Compute performance statistics over a list of trades."""
        if not trades:
            return PerformanceSnapshot()

        wins = [t for t in trades if t.get("win_or_loss") == "WIN"]
        losses = [t for t in trades if t.get("win_or_loss") == "LOSS"]

        r_multiples = [t.get("r_multiple", 0.0) for t in trades]
        slippages = [t.get("slippage", 0.0) for t in trades]
        exec_scores = [t.get("execution_score", 1.0) for t in trades]
        pnls = [t.get("pnl", 0.0) for t in trades]

        # Profit factor
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (
            float("inf") if gross_profit > 0 else 0.0
        )

        # Drawdown depth (max peak-to-trough in cumulative PnL)
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for pnl in pnls:
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd

        # Regime breakdown
        regime_breakdown = self._breakdown_by_field(trades, "volatility_regime")
        strategy_breakdown = self._breakdown_by_field(trades, "strategy_used")

        return PerformanceSnapshot(
            window_size=len(trades),
            win_rate=len(wins) / len(trades) if trades else 0.0,
            avg_r_multiple=sum(r_multiples) / len(r_multiples) if r_multiples else 0.0,
            avg_slippage=sum(slippages) / len(slippages) if slippages else 0.0,
            drawdown_depth=max_dd,
            profit_factor=min(profit_factor, 999.0),
            total_pnl=sum(pnls),
            best_r=max(r_multiples) if r_multiples else 0.0,
            worst_r=min(r_multiples) if r_multiples else 0.0,
            avg_execution_score=sum(exec_scores) / len(exec_scores) if exec_scores else 0.0,
            regime_breakdown=regime_breakdown,
            strategy_breakdown=strategy_breakdown,
        )

    def _breakdown_by_field(
        self, trades: List[Dict], field_name: str
    ) -> Dict[str, Dict[str, float]]:
        """Break down win rate and avg R by a categorical field."""
        groups: Dict[str, List[Dict]] = {}
        for t in trades:
            key = t.get(field_name, "UNKNOWN")
            groups.setdefault(key, []).append(t)

        result = {}
        for key, group in groups.items():
            wins = sum(1 for t in group if t.get("win_or_loss") == "WIN")
            rs = [t.get("r_multiple", 0.0) for t in group]
            pnls = [t.get("pnl", 0.0) for t in group]
            result[key] = {
                "trade_count": len(group),
                "win_rate": wins / len(group) if group else 0.0,
                "avg_r": sum(rs) / len(rs) if rs else 0.0,
                "total_pnl": sum(pnls),
            }
        return result


# =============================================================================
# C) REGIME CLASSIFIER
# =============================================================================

class RegimeClassifier:
    """
    Classifies current market regime using volatility, ATR, and structure.

    Regimes:
        - TRENDING: Clear directional move, ATR expanding with trend
        - RANGING: Price oscillating within bounds, low directional momentum
        - HIGH_VOLATILITY: ATR > 1.5x 20-period average
        - LOW_VOLATILITY: ATR < 0.7x 20-period average
        - NEWS_DRIVEN: Sudden ATR spike > 2.5x with volume surge

    Stores result in /state/market_regime.json
    """

    def __init__(self, state_path: str = REGIME_PATH):
        self._path = state_path
        self._current_regime = MarketRegime.UNKNOWN
        self._last_classified = None
        self._load()

    def _load(self):
        """Load saved regime state."""
        if os.path.exists(self._path):
            try:
                with open(self._path, "r") as f:
                    data = json.load(f)
                self._current_regime = MarketRegime(data.get("regime", "UNKNOWN"))
                self._last_classified = data.get("classified_at")
            except (json.JSONDecodeError, IOError, ValueError):
                pass

    def _save(self):
        """Persist regime to disk."""
        try:
            payload = {
                "regime": self._current_regime.value,
                "classified_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0"
            }
            with open(self._path, "w") as f:
                json.dump(payload, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save regime state: {e}")

    def classify(
        self,
        current_atr: float,
        avg_atr_20: float,
        price_change_pct: float,
        volume_ratio: float = 1.0,
        ema_alignment: Optional[str] = None,
    ) -> MarketRegime:
        """
        Classify the current market regime.

        Args:
            current_atr: Current ATR value
            avg_atr_20: 20-period average ATR
            price_change_pct: Recent price change percentage (e.g., over 20 bars)
            volume_ratio: Current volume / average volume
            ema_alignment: "bullish", "bearish", or None (from strategy engine)

        Returns:
            MarketRegime classification
        """
        if avg_atr_20 <= 0:
            self._current_regime = MarketRegime.UNKNOWN
            self._save()
            return self._current_regime

        atr_ratio = current_atr / avg_atr_20

        # NEWS_DRIVEN: extreme ATR spike with volume surge
        if atr_ratio > 2.5 and volume_ratio > 2.0:
            regime = MarketRegime.NEWS_DRIVEN

        # HIGH_VOLATILITY: ATR significantly above normal
        elif atr_ratio > 1.5:
            regime = MarketRegime.HIGH_VOLATILITY

        # LOW_VOLATILITY: ATR significantly below normal
        elif atr_ratio < 0.7:
            regime = MarketRegime.LOW_VOLATILITY

        # TRENDING: directional move with aligned EMAs
        elif abs(price_change_pct) > 1.5 and ema_alignment in ("bullish", "bearish"):
            regime = MarketRegime.TRENDING

        # RANGING: everything else
        else:
            regime = MarketRegime.RANGING

        self._current_regime = regime
        self._last_classified = datetime.now(timezone.utc).isoformat()
        self._save()

        logger.info(
            f"Regime classified: {regime.value} | ATR ratio={atr_ratio:.2f} | "
            f"Price change={price_change_pct:.2f}% | Volume ratio={volume_ratio:.2f}"
        )
        return regime

    @property
    def current(self) -> MarketRegime:
        return self._current_regime

    def get_state(self) -> Dict[str, Any]:
        return {
            "regime": self._current_regime.value,
            "classified_at": self._last_classified,
        }


# =============================================================================
# D) STRATEGY WEIGHTING ADJUSTMENT
# =============================================================================

# Default baseline weights (must match strategy_engine.py defaults)
BASELINE_WEIGHTS = {
    "TrendFollower": 0.25,
    "MeanReversion": 0.20,
    "LiquiditySweep": 0.25,
    "TimeCycles": 0.15,
    "FearGreed": 0.15,
}


class StrategyWeightManager:
    """
    Adjusts strategy allocation weights based on regime-specific performance.

    Rules:
        - No weight > 1.3x baseline
        - No weight < 0.7x baseline
        - Changes are gradual (max WEIGHT_STEP per cycle)
        - All changes logged and reversible
    """

    def __init__(self):
        self._current_weights = dict(BASELINE_WEIGHTS)
        self._adjustment_history: List[Dict[str, Any]] = []

    def get_weights(self) -> Dict[str, float]:
        """Get current adjusted weights."""
        return dict(self._current_weights)

    def adjust(
        self,
        performance: PerformanceSnapshot,
        current_regime: MarketRegime,
    ) -> Dict[str, float]:
        """
        Adjust strategy weights based on regime-specific performance.

        Strategies underperforming in the current regime get reduced.
        Strategies outperforming get increased.
        All within bounded limits.
        """
        regime_key = current_regime.value
        regime_stats = performance.strategy_breakdown

        if not regime_stats:
            return self._current_weights

        # Calculate average performance across all strategies
        all_win_rates = [
            s.get("win_rate", 0.5) for s in regime_stats.values()
        ]
        avg_win_rate = sum(all_win_rates) / len(all_win_rates) if all_win_rates else 0.5

        adjustments = {}
        for strategy_name, baseline in BASELINE_WEIGHTS.items():
            stats = regime_stats.get(strategy_name)
            if not stats or stats.get("trade_count", 0) < 3:
                # Not enough data — keep current weight
                continue

            win_rate = stats.get("win_rate", 0.5)

            # Determine direction
            if win_rate < avg_win_rate - 0.05:
                # Underperforming — reduce
                delta = -WEIGHT_STEP
            elif win_rate > avg_win_rate + 0.05:
                # Outperforming — increase
                delta = WEIGHT_STEP
            else:
                delta = 0.0

            if delta == 0.0:
                continue

            new_weight = self._current_weights.get(strategy_name, baseline) + delta

            # Enforce bounds
            floor = baseline * WEIGHT_MIN_MULTIPLIER
            ceiling = baseline * WEIGHT_MAX_MULTIPLIER
            new_weight = max(floor, min(ceiling, new_weight))

            adjustments[strategy_name] = {
                "old": self._current_weights.get(strategy_name, baseline),
                "new": round(new_weight, 4),
                "delta": round(delta, 4),
                "reason": f"win_rate={win_rate:.2f} vs avg={avg_win_rate:.2f} in {regime_key}",
            }
            self._current_weights[strategy_name] = round(new_weight, 4)

        if adjustments:
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "regime": regime_key,
                "adjustments": adjustments,
            }
            self._adjustment_history.append(record)
            logger.info(f"Strategy weights adjusted: {json.dumps(adjustments)}")

        return self._current_weights

    def reset_to_baseline(self):
        """Reset all weights to baseline values."""
        self._current_weights = dict(BASELINE_WEIGHTS)
        logger.info("Strategy weights reset to baseline")

    def get_history(self, count: int = 20) -> List[Dict[str, Any]]:
        return self._adjustment_history[-count:]


# =============================================================================
# E) RISK DYNAMIC MODULATION
# =============================================================================

class RiskModulator:
    """
    Temporarily adjusts risk percentage based on recent performance.

    - Drawdown rising → reduce risk %
    - Strong performance streak → increase slightly (never exceed max cap)
    - All adjustments stay within RiskGovernor limits

    The modulator provides a MULTIPLIER (0.5–1.15) applied to position sizing.
    It does NOT modify RiskGovernor rules directly.
    """

    def __init__(self):
        self._multiplier: float = 1.0
        self._mode: AdaptationMode = AdaptationMode.NORMAL
        self._history: List[Dict[str, Any]] = []

    @property
    def multiplier(self) -> float:
        return self._multiplier

    @property
    def mode(self) -> AdaptationMode:
        return self._mode

    def modulate(self, performance: PerformanceSnapshot) -> float:
        """
        Compute risk modulation multiplier based on performance.

        Returns:
            float multiplier to apply to position sizes (0.5–1.15)
        """
        old_multiplier = self._multiplier
        old_mode = self._mode

        # Drawdown rising — reduce
        if performance.drawdown_depth > 0 and performance.win_rate < 0.45:
            target = max(
                RISK_MODULATION_MIN,
                self._multiplier - RISK_MODULATION_STEP
            )
            self._multiplier = target
            self._mode = AdaptationMode.CAUTIOUS

        # Strong streak — increase slightly
        elif performance.win_rate > 0.6 and performance.profit_factor > 1.5:
            target = min(
                RISK_MODULATION_MAX,
                self._multiplier + RISK_MODULATION_STEP * 0.5  # Half-step up
            )
            self._multiplier = target
            self._mode = AdaptationMode.AGGRESSIVE

        # Normal conditions — drift back to 1.0
        else:
            if self._multiplier < 1.0:
                self._multiplier = min(1.0, self._multiplier + 0.01)
            elif self._multiplier > 1.0:
                self._multiplier = max(1.0, self._multiplier - 0.01)
            self._mode = AdaptationMode.NORMAL

        # Round for clarity
        self._multiplier = round(self._multiplier, 3)

        if old_multiplier != self._multiplier or old_mode != self._mode:
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "old_multiplier": old_multiplier,
                "new_multiplier": self._multiplier,
                "old_mode": old_mode.value,
                "new_mode": self._mode.value,
                "win_rate": performance.win_rate,
                "drawdown": performance.drawdown_depth,
                "profit_factor": performance.profit_factor,
            }
            self._history.append(record)
            logger.info(
                f"Risk modulation: {old_multiplier} -> {self._multiplier} | "
                f"Mode: {self._mode.value}"
            )

        return self._multiplier

    def enter_protective_mode(self):
        """Hard safety: cut risk by 50%."""
        self._multiplier = RISK_MODULATION_MIN
        self._mode = AdaptationMode.PROTECTIVE
        logger.critical("PROTECTIVE MODE ENGAGED: Risk reduced to 50%")

    def get_state(self) -> Dict[str, Any]:
        return {
            "multiplier": self._multiplier,
            "mode": self._mode.value,
            "history_count": len(self._history),
        }

    def get_history(self, count: int = 20) -> List[Dict[str, Any]]:
        return self._history[-count:]


# =============================================================================
# F) SELF-HEALTH CHECK
# =============================================================================

class HealthMonitor:
    """
    Monitors execution quality and system health.

    If execution score drops, slippage rises, or spreads are unstable:
        → Automatically reduce activity frequency.
    """

    def __init__(self):
        self._healthy = True
        self._activity_throttle: float = 1.0  # 1.0 = normal, <1.0 = reduced
        self._issues: List[str] = []

    def check(self, trades: List[Dict[str, Any]]) -> bool:
        """
        Evaluate health from recent trades.

        Returns:
            True if healthy, False if degraded
        """
        self._issues = []

        if len(trades) < 3:
            self._healthy = True
            self._activity_throttle = 1.0
            return True

        recent = trades[-HEALTH_CHECK_WINDOW:]

        # Average execution score
        exec_scores = [t.get("execution_score", 1.0) for t in recent]
        avg_exec = sum(exec_scores) / len(exec_scores)

        # Average slippage
        slippages = [abs(t.get("slippage", 0.0)) for t in recent]
        avg_slippage = sum(slippages) / len(slippages)

        # Check thresholds
        if avg_exec < 0.6:
            self._issues.append(f"Low execution score: {avg_exec:.2f}")

        if avg_slippage > 0.005:  # 0.5% slippage threshold
            self._issues.append(f"High slippage: {avg_slippage:.4f}")

        if self._issues:
            self._healthy = False
            # Reduce activity proportionally
            self._activity_throttle = max(0.3, avg_exec)
            logger.warning(f"Health degraded: {', '.join(self._issues)}")
        else:
            self._healthy = True
            # Gradually restore throttle
            if self._activity_throttle < 1.0:
                self._activity_throttle = min(1.0, self._activity_throttle + 0.1)

        return self._healthy

    @property
    def is_healthy(self) -> bool:
        return self._healthy

    @property
    def throttle(self) -> float:
        return self._activity_throttle

    def get_state(self) -> Dict[str, Any]:
        return {
            "healthy": self._healthy,
            "activity_throttle": self._activity_throttle,
            "issues": self._issues,
        }


# =============================================================================
# G) ADAPTATION SAFETY — LOGGING & RATE LIMITING
# =============================================================================

class AdaptationLogger:
    """
    All adaptation decisions are logged to /logs/adaptation.log.

    Ensures:
        - Every change is recorded with before/after state
        - Rate limiting prevents rapid parameter churn
        - All decisions are auditable
    """

    def __init__(self, log_path: str = ADAPTATION_LOG_PATH):
        self._path = log_path
        self._last_adaptation_time: float = 0.0

    def can_adapt(self) -> bool:
        """Check if enough time has passed since last adaptation."""
        elapsed = time.time() - self._last_adaptation_time
        return elapsed >= ADAPTATION_COOLDOWN_SECONDS

    def log_adaptation(self, event: Dict[str, Any]):
        """Log an adaptation event to the adaptation log file."""
        self._last_adaptation_time = time.time()

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event,
        }

        try:
            with open(self._path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError as e:
            logger.error(f"Failed to write adaptation log: {e}")

        logger.info(f"Adaptation logged: {event.get('type', 'UNKNOWN')}")

    @property
    def cooldown_remaining(self) -> float:
        elapsed = time.time() - self._last_adaptation_time
        remaining = ADAPTATION_COOLDOWN_SECONDS - elapsed
        return max(0.0, remaining)


# =============================================================================
# I) DAILY REVIEW SUMMARY
# =============================================================================

class DailyReviewGenerator:
    """
    Generates daily_meta_report.md at end of each trading day.

    Includes:
        - What worked / what failed
        - Regime classification
        - Risk adjustment decisions
        - Execution health
    """

    def generate(
        self,
        performance: PerformanceSnapshot,
        regime: MarketRegime,
        weights: Dict[str, float],
        risk_state: Dict[str, Any],
        health_state: Dict[str, Any],
        adaptation_mode: AdaptationMode,
        date_str: Optional[str] = None,
    ) -> str:
        """Generate a markdown daily meta report."""
        if date_str is None:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Build strategy performance table
        strategy_lines = []
        for name, stats in performance.strategy_breakdown.items():
            wr = stats.get("win_rate", 0) * 100
            avg_r = stats.get("avg_r", 0)
            count = stats.get("trade_count", 0)
            weight = weights.get(name, 0)
            strategy_lines.append(
                f"| {name} | {count} | {wr:.1f}% | {avg_r:.2f} | {weight:.3f} |"
            )

        strategy_table = "\n".join(strategy_lines) if strategy_lines else "| No trades recorded |"

        # What worked / what failed
        winners = [
            (name, s) for name, s in performance.strategy_breakdown.items()
            if s.get("win_rate", 0) > 0.55
        ]
        losers = [
            (name, s) for name, s in performance.strategy_breakdown.items()
            if s.get("win_rate", 0) < 0.45 and s.get("trade_count", 0) >= 3
        ]

        worked = ", ".join(
            f"{n} ({s['win_rate']*100:.0f}% WR)" for n, s in winners
        ) or "No standout performers"

        failed = ", ".join(
            f"{n} ({s['win_rate']*100:.0f}% WR)" for n, s in losers
        ) or "No significant underperformers"

        report = f"""# NEXUS Daily Meta Report — {date_str}

## Performance Summary

| Metric | Value |
|--------|-------|
| Total Trades | {performance.window_size} |
| Win Rate | {performance.win_rate*100:.1f}% |
| Avg R-Multiple | {performance.avg_r_multiple:.2f} |
| Profit Factor | {performance.profit_factor:.2f} |
| Total P&L | {performance.total_pnl:.2f} |
| Max Drawdown | {performance.drawdown_depth:.2f} |
| Avg Execution Score | {performance.avg_execution_score:.2f} |
| Avg Slippage | {performance.avg_slippage:.4f} |

## What Worked

{worked}

## What Failed

{failed}

## Strategy Breakdown

| Strategy | Trades | Win Rate | Avg R | Weight |
|----------|--------|----------|-------|--------|
{strategy_table}

## Regime Classification

**Current Regime:** {regime.value}

| Regime | Trades | Win Rate | Avg R |
|--------|--------|----------|-------|
{self._regime_table(performance.regime_breakdown)}

## Risk Adjustment Decisions

- **Adaptation Mode:** {adaptation_mode.value}
- **Risk Multiplier:** {risk_state.get('multiplier', 1.0)}
- **Health Status:** {"HEALTHY" if health_state.get('healthy', True) else "DEGRADED"}
- **Activity Throttle:** {health_state.get('activity_throttle', 1.0)}

## Execution Health

- **Issues:** {', '.join(health_state.get('issues', [])) or 'None'}

---

*Generated by NEXUS Meta-Intelligence Layer — Phase 10*
*All decisions are auditable via /logs/adaptation.log*
"""
        # Save to file
        report_path = os.path.join(DAILY_REPORT_DIR, f"daily_meta_report_{date_str}.md")
        try:
            with open(report_path, "w") as f:
                f.write(report)
            logger.info(f"Daily meta report saved: {report_path}")
        except IOError as e:
            logger.error(f"Failed to save daily report: {e}")

        return report

    def _regime_table(self, breakdown: Dict[str, Dict[str, float]]) -> str:
        lines = []
        for regime, stats in breakdown.items():
            count = stats.get("trade_count", 0)
            wr = stats.get("win_rate", 0) * 100
            avg_r = stats.get("avg_r", 0)
            lines.append(f"| {regime} | {count} | {wr:.1f}% | {avg_r:.2f} |")
        return "\n".join(lines) if lines else "| No regime data |"


# =============================================================================
# MASTER ORCHESTRATOR — PERFORMANCE INTELLIGENCE
# =============================================================================

class PerformanceIntelligence:
    """
    Central meta-intelligence coordinator.

    Integrates all subsystems:
        A) Trade Journal
        B) Performance Analyzer
        C) Regime Classifier
        D) Strategy Weighting
        E) Risk Modulation
        F) Self-Health Check
        G) Adaptation Safety
        H) Dashboard Data
        I) Daily Review
        J) Hard Safety (PROTECTIVE MODE)

    NEVER modifies strategy logic, RiskGovernor rules, or ExecutionOptimizer.
    Only adjusts weights and parameters within bounded, reversible ranges.
    """

    _instance = None

    def __init__(self):
        self.journal = TradeJournal()
        self.analyzer = PerformanceAnalyzer()
        self.regime_classifier = RegimeClassifier()
        self.weight_manager = StrategyWeightManager()
        self.risk_modulator = RiskModulator()
        self.health_monitor = HealthMonitor()
        self.adaptation_logger = AdaptationLogger()
        self.daily_review = DailyReviewGenerator()

        self._last_analysis_trade_count: int = 0
        self._protective_mode: bool = False
        self._latest_snapshot: Optional[PerformanceSnapshot] = None
        self._running: bool = False
        self._monitor_task: Optional[asyncio.Task] = None

        logger.info("PerformanceIntelligence initialized — Phase 10 active")

    @classmethod
    def get_instance(cls) -> "PerformanceIntelligence":
        if cls._instance is None:
            cls._instance = PerformanceIntelligence()
        return cls._instance

    # -------------------------------------------------------------------------
    # A) Record a closed trade
    # -------------------------------------------------------------------------
    def record_trade(
        self,
        trade_id: str,
        strategy_used: str,
        asset: str,
        lot_size: float,
        entry_price: float,
        exit_price: float,
        r_multiple: float,
        slippage: float,
        execution_score: float,
        volatility_regime: Optional[str] = None,
        macro_state: str = "UNKNOWN",
        holding_duration_seconds: float = 0.0,
    ):
        """
        Record a closed trade into the performance ledger.

        This is the primary integration point — called when any trade closes.
        """
        pnl = (exit_price - entry_price) * lot_size
        win_or_loss = "WIN" if pnl > 0 else "LOSS"

        if volatility_regime is None:
            volatility_regime = self.regime_classifier.current.value

        now = datetime.now(timezone.utc)

        record = TradeRecord(
            trade_id=trade_id,
            timestamp=now.isoformat(),
            strategy_used=strategy_used,
            asset=asset,
            lot_size=lot_size,
            entry_price=entry_price,
            exit_price=exit_price,
            r_multiple=r_multiple,
            slippage=slippage,
            execution_score=execution_score,
            time_of_day=now.strftime("%H:%M"),
            volatility_regime=volatility_regime,
            macro_state=macro_state,
            win_or_loss=win_or_loss,
            pnl=pnl,
            holding_duration_seconds=holding_duration_seconds,
        )

        self.journal.record_trade(record)

        # Check if we should run analysis
        if self.journal.total_trades - self._last_analysis_trade_count >= ANALYSIS_TRADE_WINDOW:
            self._run_analysis_cycle()

    # -------------------------------------------------------------------------
    # B+C+D+E+F) Full analysis cycle
    # -------------------------------------------------------------------------
    def _run_analysis_cycle(self):
        """
        Run full analysis, regime classification, weight adjustment, and risk modulation.
        Rate-limited by adaptation cooldown.
        """
        if not self.adaptation_logger.can_adapt():
            remaining = self.adaptation_logger.cooldown_remaining
            logger.info(f"Adaptation cooldown active: {remaining:.0f}s remaining")
            return

        self._last_analysis_trade_count = self.journal.total_trades
        recent_trades = self.journal.get_recent(ANALYSIS_TRADE_WINDOW)

        # B) Analyze performance
        snapshot = self.analyzer.analyze(recent_trades)
        self._latest_snapshot = snapshot

        # F) Health check
        all_trades = self.journal.get_all()
        self.health_monitor.check(all_trades)

        if self.health_monitor.is_healthy is False:
            self.risk_modulator._mode = AdaptationMode.REDUCED_ACTIVITY

        # D) Adjust strategy weights
        old_weights = self.weight_manager.get_weights()
        new_weights = self.weight_manager.adjust(snapshot, self.regime_classifier.current)

        # E) Risk modulation
        old_risk = self.risk_modulator.multiplier
        new_risk = self.risk_modulator.modulate(snapshot)

        # J) HARD SAFETY — PROTECTIVE MODE
        rolling_30 = self.journal.get_recent(30)
        if len(rolling_30) >= 30:
            rolling_snapshot = self.analyzer.analyze(rolling_30)
            if rolling_snapshot.win_rate < PROTECTIVE_MODE_THRESHOLD:
                self._engage_protective_mode(rolling_snapshot)

        # G) Log the adaptation
        self.adaptation_logger.log_adaptation({
            "type": "ANALYSIS_CYCLE",
            "trade_count": self.journal.total_trades,
            "snapshot": {
                "win_rate": snapshot.win_rate,
                "avg_r": snapshot.avg_r_multiple,
                "profit_factor": snapshot.profit_factor,
                "drawdown": snapshot.drawdown_depth,
            },
            "regime": self.regime_classifier.current.value,
            "weight_changes": {
                k: {"old": old_weights.get(k), "new": new_weights.get(k)}
                for k in BASELINE_WEIGHTS
                if old_weights.get(k) != new_weights.get(k)
            },
            "risk_modulation": {
                "old": old_risk,
                "new": new_risk,
                "mode": self.risk_modulator.mode.value,
            },
            "health": self.health_monitor.get_state(),
        })

        logger.info(
            f"Analysis cycle complete | Trades: {self.journal.total_trades} | "
            f"WR: {snapshot.win_rate:.2f} | PF: {snapshot.profit_factor:.2f} | "
            f"Regime: {self.regime_classifier.current.value} | "
            f"Risk: {new_risk}"
        )

    # -------------------------------------------------------------------------
    # C) Classify regime (called externally with market data)
    # -------------------------------------------------------------------------
    def classify_regime(
        self,
        current_atr: float,
        avg_atr_20: float,
        price_change_pct: float,
        volume_ratio: float = 1.0,
        ema_alignment: Optional[str] = None,
    ) -> str:
        """Classify the current market regime. Returns regime string."""
        regime = self.regime_classifier.classify(
            current_atr, avg_atr_20, price_change_pct, volume_ratio, ema_alignment
        )
        return regime.value

    # -------------------------------------------------------------------------
    # J) HARD SAFETY — PROTECTIVE MODE
    # -------------------------------------------------------------------------
    def _engage_protective_mode(self, snapshot: PerformanceSnapshot):
        """
        PROTECTIVE MODE: Rolling 30-trade performance below threshold.

        Actions:
            1. Reduce risk by 50%
            2. Restrict strategy set (reset weights to baseline)
            3. Notify via Telegram
        """
        if self._protective_mode:
            return  # Already in protective mode

        self._protective_mode = True
        self.risk_modulator.enter_protective_mode()
        self.weight_manager.reset_to_baseline()

        self.adaptation_logger.log_adaptation({
            "type": "PROTECTIVE_MODE_ENGAGED",
            "trigger": f"Rolling 30-trade win rate: {snapshot.win_rate:.2f}",
            "actions": [
                "Risk reduced to 50%",
                "Strategy weights reset to baseline",
                "Telegram notification queued",
            ],
        })

        logger.critical(
            f"PROTECTIVE MODE ENGAGED | Win rate: {snapshot.win_rate:.2f} | "
            f"Threshold: {PROTECTIVE_MODE_THRESHOLD}"
        )

        # Queue Telegram notification (non-blocking)
        self._notify_protective_mode(snapshot)

    def _notify_protective_mode(self, snapshot: PerformanceSnapshot):
        """Send protective mode alert via Telegram."""
        try:
            from app.services.telegram_bot import get_telegram_service
            telegram = get_telegram_service()

            message = (
                "NEXUS PROTECTIVE MODE ENGAGED\n\n"
                f"Rolling 30-trade win rate: {snapshot.win_rate*100:.1f}%\n"
                f"Threshold: {PROTECTIVE_MODE_THRESHOLD*100:.0f}%\n"
                f"Profit Factor: {snapshot.profit_factor:.2f}\n"
                f"Drawdown: {snapshot.drawdown_depth:.2f}\n\n"
                "Actions taken:\n"
                "- Risk reduced to 50%\n"
                "- Strategy weights reset\n"
                "- Activity restricted\n\n"
                "Capital preservation active. Manual review recommended."
            )

            # Schedule the async send
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(telegram.send_message(message))
            except RuntimeError:
                logger.warning("No running event loop for Telegram notification")
        except ImportError:
            logger.warning("Telegram service not available for protective mode alert")

    def exit_protective_mode(self):
        """Manually exit protective mode after review."""
        if not self._protective_mode:
            return

        self._protective_mode = False
        self.risk_modulator._multiplier = 0.75  # Cautious re-entry
        self.risk_modulator._mode = AdaptationMode.CAUTIOUS

        self.adaptation_logger.log_adaptation({
            "type": "PROTECTIVE_MODE_EXITED",
            "new_risk_multiplier": 0.75,
            "mode": "CAUTIOUS",
        })
        logger.info("PROTECTIVE MODE EXITED — Cautious re-entry at 75% risk")

    # -------------------------------------------------------------------------
    # H) Dashboard data for SYSTEM EVOLUTION panel
    # -------------------------------------------------------------------------
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data for the SYSTEM EVOLUTION telemetry panel.

        Returns:
            Dict with regime, weight distribution, risk modulation,
            adaptation state, and 30-trade performance snapshot.
        """
        recent_30 = self.journal.get_recent(30)
        snapshot_30 = self.analyzer.analyze(recent_30) if recent_30 else PerformanceSnapshot()

        return {
            "current_regime": self.regime_classifier.get_state(),
            "strategy_weights": self.weight_manager.get_weights(),
            "baseline_weights": dict(BASELINE_WEIGHTS),
            "risk_modulation": self.risk_modulator.get_state(),
            "adaptation_state": {
                "mode": self.risk_modulator.mode.value,
                "protective_mode": self._protective_mode,
                "cooldown_remaining": round(self.adaptation_logger.cooldown_remaining, 0),
                "total_trades_analyzed": self.journal.total_trades,
                "last_analysis_at": self._last_analysis_trade_count,
            },
            "health": self.health_monitor.get_state(),
            "performance_30_trade": {
                "win_rate": round(snapshot_30.win_rate, 3),
                "avg_r_multiple": round(snapshot_30.avg_r_multiple, 3),
                "profit_factor": round(snapshot_30.profit_factor, 2),
                "drawdown_depth": round(snapshot_30.drawdown_depth, 2),
                "total_pnl": round(snapshot_30.total_pnl, 2),
                "avg_slippage": round(snapshot_30.avg_slippage, 5),
                "avg_execution_score": round(snapshot_30.avg_execution_score, 3),
                "trade_count": snapshot_30.window_size,
            },
            "weight_adjustment_history": self.weight_manager.get_history(10),
            "risk_modulation_history": self.risk_modulator.get_history(10),
        }

    # -------------------------------------------------------------------------
    # I) Generate daily review
    # -------------------------------------------------------------------------
    def generate_daily_review(self, date_str: Optional[str] = None) -> str:
        """Generate and save the daily meta report."""
        today_trades = self.journal.get_all()
        if date_str:
            # Filter trades for the given date
            today_trades = [
                t for t in today_trades
                if t.get("timestamp", "").startswith(date_str)
            ]

        snapshot = self.analyzer.analyze(today_trades) if today_trades else PerformanceSnapshot()

        return self.daily_review.generate(
            performance=snapshot,
            regime=self.regime_classifier.current,
            weights=self.weight_manager.get_weights(),
            risk_state=self.risk_modulator.get_state(),
            health_state=self.health_monitor.get_state(),
            adaptation_mode=self.risk_modulator.mode,
            date_str=date_str,
        )

    # -------------------------------------------------------------------------
    # Background monitor (optional async loop)
    # -------------------------------------------------------------------------
    async def start(self):
        """Start the background monitoring loop."""
        if self._running:
            return
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("PerformanceIntelligence background monitor started")

    async def stop(self):
        """Stop background monitoring."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("PerformanceIntelligence background monitor stopped")

    async def _monitor_loop(self):
        """
        Background loop that periodically checks if analysis should run.
        Also generates daily review at end of trading day (21:00 UTC).
        """
        last_daily_report_date = None

        while self._running:
            try:
                now = datetime.now(timezone.utc)

                # Check for daily review generation (21:00 UTC = NYSE close)
                if now.hour == 21 and now.weekday() < 5:
                    today = now.strftime("%Y-%m-%d")
                    if last_daily_report_date != today:
                        self.generate_daily_review(today)
                        last_daily_report_date = today

                # Check if pending analysis is needed
                pending = self.journal.total_trades - self._last_analysis_trade_count
                if pending >= ANALYSIS_TRADE_WINDOW:
                    self._run_analysis_cycle()

            except Exception as e:
                logger.error(f"Monitor loop error: {e}")

            await asyncio.sleep(60)  # Check every minute

    # -------------------------------------------------------------------------
    # Convenience: get strategy weights for orchestrator
    # -------------------------------------------------------------------------
    def get_strategy_weights(self) -> Dict[str, float]:
        """Get current strategy weights (for StrategyOrchestrator consumption)."""
        return self.weight_manager.get_weights()

    def get_risk_multiplier(self) -> float:
        """Get current risk modulation multiplier (for position sizing)."""
        return self.risk_modulator.multiplier

    def get_activity_throttle(self) -> float:
        """Get health-based activity throttle (1.0=normal, <1.0=reduced)."""
        return self.health_monitor.throttle

    def is_protective_mode(self) -> bool:
        """Check if system is in protective mode."""
        return self._protective_mode

    def force_analysis(self):
        """Manually trigger an analysis cycle (admin action)."""
        self._run_analysis_cycle()


# =============================================================================
# GLOBAL ACCESSOR
# =============================================================================

def get_performance_intelligence() -> PerformanceIntelligence:
    """Get the singleton PerformanceIntelligence instance."""
    return PerformanceIntelligence.get_instance()
