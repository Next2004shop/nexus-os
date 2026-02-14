"""
NEXUS Self-Audit Loop — Phase 5, Part F
=========================================

Quality control and self-monitoring:

1. Post-trade audit — expected vs actual, deviation logging
2. Daily review — repeated errors, rule tightening suggestions
3. Weekly report — strategy by regime, risk efficiency, assets to avoid

Suggestions are logged/reported ONLY — never auto-applied.
"""

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nexus.self_audit")


# =============================================================================
# AUDIT RECORD
# =============================================================================

@dataclass
class TradeAudit:
    """Post-trade audit comparing expected vs actual."""
    trade_id: str
    symbol: str
    side: str
    expected_direction: str    # what AI predicted
    actual_outcome: str        # WIN, LOSS, BREAKEVEN
    expected_r: float          # expected R-multiple target
    actual_r: float            # actual R-multiple achieved
    deviation: float           # |expected_r - actual_r|
    regime_at_entry: str
    confluence_score: float
    confidence_at_entry: float
    exit_reason: str
    anomaly_flags: List[str]   # any detected issues
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "side": self.side,
            "expected_direction": self.expected_direction,
            "actual_outcome": self.actual_outcome,
            "expected_r": round(self.expected_r, 2),
            "actual_r": round(self.actual_r, 2),
            "deviation": round(self.deviation, 2),
            "regime_at_entry": self.regime_at_entry,
            "confluence_score": round(self.confluence_score, 2),
            "confidence_at_entry": round(self.confidence_at_entry, 3),
            "exit_reason": self.exit_reason,
            "anomaly_flags": self.anomaly_flags,
            "timestamp": self.timestamp,
        }


# =============================================================================
# DAILY REVIEW
# =============================================================================

@dataclass
class DailyReview:
    """Summary of daily trading quality."""
    date: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    avg_deviation: float = 0.0
    repeated_errors: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    regime_breakdown: Dict[str, Dict[str, int]] = field(default_factory=dict)
    worst_asset: str = ""
    best_asset: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": round(self.wins / self.total_trades * 100, 1) if self.total_trades > 0 else 0,
            "avg_deviation": round(self.avg_deviation, 2),
            "repeated_errors": self.repeated_errors,
            "suggestions": self.suggestions,
            "regime_breakdown": self.regime_breakdown,
            "worst_asset": self.worst_asset,
            "best_asset": self.best_asset,
        }


# =============================================================================
# WEEKLY REPORT
# =============================================================================

@dataclass
class WeeklyReport:
    """Weekly performance analysis and recommendations."""
    week_start: str
    week_end: str
    total_trades: int = 0
    win_rate: float = 0.0
    net_pnl: float = 0.0
    strategy_by_regime: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    risk_efficiency: float = 0.0     # (net_pnl / max_drawdown) if dd > 0
    drawdown_contributors: List[Dict[str, Any]] = field(default_factory=list)
    assets_to_avoid: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "week_start": self.week_start,
            "week_end": self.week_end,
            "total_trades": self.total_trades,
            "win_rate": round(self.win_rate, 1),
            "net_pnl": round(self.net_pnl, 2),
            "strategy_by_regime": self.strategy_by_regime,
            "risk_efficiency": round(self.risk_efficiency, 2),
            "drawdown_contributors": self.drawdown_contributors,
            "assets_to_avoid": self.assets_to_avoid,
            "suggestions": self.suggestions,
        }

    def format_for_telegram(self) -> str:
        """Format weekly report for Telegram/log output."""
        lines = [
            f"WEEKLY REPORT ({self.week_start} to {self.week_end})",
            f"  Trades: {self.total_trades} | Win Rate: {self.win_rate:.1f}%",
            f"  Net P&L: ${self.net_pnl:+,.2f}",
            f"  Risk Efficiency: {self.risk_efficiency:.2f}",
        ]
        if self.strategy_by_regime:
            lines.append("  Performance by Regime:")
            for regime, data in self.strategy_by_regime.items():
                wr = data.get("win_rate", 0)
                trades = data.get("trades", 0)
                pnl = data.get("pnl", 0)
                lines.append(f"    {regime}: {trades} trades, {wr:.0f}% WR, ${pnl:+,.2f}")
        if self.drawdown_contributors:
            lines.append("  Top Drawdown Contributors:")
            for dd in self.drawdown_contributors[:3]:
                lines.append(f"    {dd.get('symbol', '?')}: ${dd.get('loss', 0):,.2f}")
        if self.assets_to_avoid:
            lines.append(f"  Assets to Avoid: {', '.join(self.assets_to_avoid)}")
        if self.suggestions:
            lines.append("  Suggestions:")
            for s in self.suggestions:
                lines.append(f"    - {s}")
        return "\n".join(lines)


# =============================================================================
# SELF-AUDIT ENGINE
# =============================================================================

class SelfAuditEngine:
    """
    Tracks trade outcomes, identifies patterns, generates reviews.

    All outputs are advisory — no auto-application of rule changes.
    """

    def __init__(self):
        self._audits: List[TradeAudit] = []
        self._daily_reviews: Dict[str, DailyReview] = {}
        self._weekly_reports: List[WeeklyReport] = []
        self._lock = threading.Lock()

    # ── Post-Trade Audit ─────────────────────────────────────────

    def audit_trade(
        self,
        trade_id: str,
        symbol: str,
        side: str,
        expected_direction: str,
        pnl: float,
        expected_r: float,
        actual_r: float,
        regime: str,
        confluence_score: float,
        confidence: float,
        exit_reason: str,
    ) -> TradeAudit:
        """
        Audit a completed trade: compare expected vs actual.
        """
        # Determine outcome
        if pnl > 0:
            outcome = "WIN"
        elif pnl < 0:
            outcome = "LOSS"
        else:
            outcome = "BREAKEVEN"

        deviation = abs(expected_r - actual_r)

        # Flag anomalies
        anomalies: List[str] = []
        if deviation > 2.0:
            anomalies.append(f"HIGH_DEVIATION: expected {expected_r:.1f}R, got {actual_r:.1f}R")
        if confidence > 0.85 and outcome == "LOSS":
            anomalies.append(f"HIGH_CONFIDENCE_LOSS: {confidence:.0%} confidence but lost")
        if confluence_score > 0.8 and outcome == "LOSS":
            anomalies.append(f"HIGH_CONFLUENCE_LOSS: {confluence_score:.0%} confluence but lost")
        if exit_reason == "SL" and actual_r < -1.5:
            anomalies.append(f"SL_OVERRUN: actual R={actual_r:.1f} beyond expected SL")

        audit = TradeAudit(
            trade_id=trade_id,
            symbol=symbol,
            side=side,
            expected_direction=expected_direction,
            actual_outcome=outcome,
            expected_r=expected_r,
            actual_r=actual_r,
            deviation=deviation,
            regime_at_entry=regime,
            confluence_score=confluence_score,
            confidence_at_entry=confidence,
            exit_reason=exit_reason,
            anomaly_flags=anomalies,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:
            self._audits.append(audit)

        if anomalies:
            logger.warning(f"AUDIT_ANOMALIES [{symbol}]: {anomalies}")
        else:
            logger.info(f"AUDIT_OK [{symbol}]: {outcome}, dev={deviation:.2f}")

        return audit

    # ── Daily Review ─────────────────────────────────────────────

    def generate_daily_review(self) -> DailyReview:
        """Generate a daily review from today's audits."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        with self._lock:
            todays_audits = [
                a for a in self._audits
                if a.timestamp.startswith(today)
            ]

        if not todays_audits:
            return DailyReview(date=today)

        review = DailyReview(date=today)
        review.total_trades = len(todays_audits)
        review.wins = sum(1 for a in todays_audits if a.actual_outcome == "WIN")
        review.losses = sum(1 for a in todays_audits if a.actual_outcome == "LOSS")

        # Average deviation
        deviations = [a.deviation for a in todays_audits]
        review.avg_deviation = sum(deviations) / len(deviations) if deviations else 0

        # Regime breakdown
        regime_data: Dict[str, Dict[str, int]] = {}
        for a in todays_audits:
            r = a.regime_at_entry or "UNKNOWN"
            if r not in regime_data:
                regime_data[r] = {"trades": 0, "wins": 0, "losses": 0}
            regime_data[r]["trades"] += 1
            if a.actual_outcome == "WIN":
                regime_data[r]["wins"] += 1
            elif a.actual_outcome == "LOSS":
                regime_data[r]["losses"] += 1
        review.regime_breakdown = regime_data

        # Find repeated error patterns
        all_anomalies: List[str] = []
        for a in todays_audits:
            all_anomalies.extend(a.anomaly_flags)

        # Count anomaly types
        anomaly_counts: Dict[str, int] = defaultdict(int)
        for af in all_anomalies:
            key = af.split(":")[0]
            anomaly_counts[key] += 1

        review.repeated_errors = [
            f"{key} ({count}x)" for key, count in anomaly_counts.items() if count >= 2
        ]

        # Asset performance
        asset_pnl: Dict[str, float] = defaultdict(float)
        for a in todays_audits:
            asset_pnl[a.symbol] += a.actual_r

        if asset_pnl:
            review.best_asset = max(asset_pnl, key=asset_pnl.get)
            review.worst_asset = min(asset_pnl, key=asset_pnl.get)

        # Generate suggestions (advisory only)
        review.suggestions = self._generate_suggestions(todays_audits, review)

        with self._lock:
            self._daily_reviews[today] = review

        logger.info(f"DAILY_REVIEW: {review.to_dict()}")
        return review

    def _generate_suggestions(
        self, audits: List[TradeAudit], review: DailyReview
    ) -> List[str]:
        """Generate rule-tightening suggestions. Advisory only."""
        suggestions = []

        # High-confidence losses
        hc_losses = [a for a in audits if a.confidence_at_entry > 0.8 and a.actual_outcome == "LOSS"]
        if len(hc_losses) >= 2:
            suggestions.append(
                f"Consider raising confidence threshold: "
                f"{len(hc_losses)} losses with >80% confidence today."
            )

        # Regime-specific issues
        for regime, data in review.regime_breakdown.items():
            if data["trades"] >= 3 and data["losses"] > data["wins"]:
                suggestions.append(
                    f"Underperforming in {regime} regime "
                    f"({data['losses']}/{data['trades']} losses). "
                    f"Consider reducing exposure in this regime."
                )

        # High deviation
        if review.avg_deviation > 1.5:
            suggestions.append(
                f"High average deviation ({review.avg_deviation:.1f}R). "
                f"Expected outcomes diverging from actual. Review sizing logic."
            )

        return suggestions

    # ── Weekly Report ────────────────────────────────────────────

    def generate_weekly_report(self) -> WeeklyReport:
        """Generate a weekly report from the last 7 days of audits."""
        now = datetime.now(timezone.utc)
        week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        week_end = now.strftime("%Y-%m-%d")

        with self._lock:
            week_audits = [
                a for a in self._audits
                if a.timestamp >= week_start
            ]

        report = WeeklyReport(week_start=week_start, week_end=week_end)

        if not week_audits:
            return report

        report.total_trades = len(week_audits)
        wins = sum(1 for a in week_audits if a.actual_outcome == "WIN")
        report.win_rate = (wins / report.total_trades * 100) if report.total_trades > 0 else 0
        report.net_pnl = sum(a.actual_r for a in week_audits)

        # Strategy by regime
        regime_stats: Dict[str, Dict[str, Any]] = {}
        for a in week_audits:
            r = a.regime_at_entry or "UNKNOWN"
            if r not in regime_stats:
                regime_stats[r] = {"trades": 0, "wins": 0, "pnl": 0.0}
            regime_stats[r]["trades"] += 1
            if a.actual_outcome == "WIN":
                regime_stats[r]["wins"] += 1
            regime_stats[r]["pnl"] += a.actual_r

        for r, data in regime_stats.items():
            data["win_rate"] = (data["wins"] / data["trades"] * 100) if data["trades"] > 0 else 0
        report.strategy_by_regime = regime_stats

        # Drawdown contributors
        loss_by_asset: Dict[str, float] = defaultdict(float)
        for a in week_audits:
            if a.actual_outcome == "LOSS":
                loss_by_asset[a.symbol] += abs(a.actual_r)

        report.drawdown_contributors = sorted(
            [{"symbol": s, "loss": l} for s, l in loss_by_asset.items()],
            key=lambda x: x["loss"],
            reverse=True,
        )[:5]

        # Assets to avoid (>= 3 trades, < 30% win rate)
        asset_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"trades": 0, "wins": 0})
        for a in week_audits:
            asset_stats[a.symbol]["trades"] += 1
            if a.actual_outcome == "WIN":
                asset_stats[a.symbol]["wins"] += 1

        report.assets_to_avoid = [
            sym for sym, data in asset_stats.items()
            if data["trades"] >= 3 and (data["wins"] / data["trades"]) < 0.30
        ]

        # Risk efficiency (net_pnl / largest DD contributor)
        if report.drawdown_contributors:
            max_dd = report.drawdown_contributors[0].get("loss", 0)
            if max_dd > 0:
                report.risk_efficiency = report.net_pnl / max_dd

        # Weekly suggestions
        report.suggestions = []
        if report.assets_to_avoid:
            report.suggestions.append(
                f"Reduce frequency on: {', '.join(report.assets_to_avoid)}"
            )
        for r, data in regime_stats.items():
            if data["trades"] >= 5 and data["win_rate"] < 35:
                report.suggestions.append(
                    f"Weak in {r} regime ({data['win_rate']:.0f}% WR). "
                    f"Consider avoiding or reducing exposure."
                )

        with self._lock:
            self._weekly_reports.append(report)

        logger.info(f"WEEKLY_REPORT:\n{report.format_for_telegram()}")
        return report

    # ── Accessors ────────────────────────────────────────────────

    def get_recent_audits(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent audit records."""
        with self._lock:
            return [a.to_dict() for a in self._audits[-limit:]]

    def get_latest_daily_review(self) -> Optional[Dict[str, Any]]:
        """Get the most recent daily review."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._lock:
            review = self._daily_reviews.get(today)
            return review.to_dict() if review else None

    def get_latest_weekly_report(self) -> Optional[Dict[str, Any]]:
        """Get the most recent weekly report."""
        with self._lock:
            if self._weekly_reports:
                return self._weekly_reports[-1].to_dict()
            return None


# =============================================================================
# SINGLETON
# =============================================================================

_engine: Optional[SelfAuditEngine] = None


def get_self_audit() -> SelfAuditEngine:
    global _engine
    if _engine is None:
        _engine = SelfAuditEngine()
    return _engine
