"""
NEXUS Weekly Intelligence Report — Phase 6, Part G
====================================================

Generates a structured weekly performance report.

Contents:
  - Win rate by regime
  - Profit factor
  - Drawdown %
  - Best/worst performing assets
  - Capital tier performance
  - Risk efficiency rating
  - Session performance

Tone: Professional, calm, institutional.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nexus.weekly_report")


# =============================================================================
# REPORT GENERATOR
# =============================================================================

def generate_weekly_intelligence_report() -> Dict[str, Any]:
    """
    Generate a comprehensive weekly intelligence report.

    Pulls data from:
      - self_audit (trade-level data)
      - performance_memory (per-asset profiles)
      - capital_tiers (tier state)
      - session_intelligence (session performance)
      - risk_governor (equity/drawdown)
      - capital_protection (daily tracker)
    """
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    week_end = now.strftime("%Y-%m-%d")

    report: Dict[str, Any] = {
        "title": "NEXUS WEEKLY INTELLIGENCE REPORT",
        "period": {"start": week_start, "end": week_end},
        "generated_at": now.isoformat(),
    }

    # ── 1. Overall Performance ────────────────────────────────────
    try:
        from app.services.self_audit import get_self_audit
        audit = get_self_audit()
        weekly = audit.generate_weekly_report()
        report["performance"] = {
            "total_trades": weekly.total_trades,
            "win_rate": round(weekly.win_rate, 1),
            "net_pnl_r": round(weekly.net_pnl, 2),
            "risk_efficiency": round(weekly.risk_efficiency, 2),
        }
        report["strategy_by_regime"] = weekly.strategy_by_regime
        report["drawdown_contributors"] = weekly.drawdown_contributors
        report["assets_to_avoid"] = weekly.assets_to_avoid
        report["audit_suggestions"] = weekly.suggestions
    except Exception as e:
        logger.error(f"Weekly report - audit error: {e}")
        report["performance"] = {"error": str(e)}

    # ── 2. Profit Factor ──────────────────────────────────────────
    try:
        from app.services.self_audit import get_self_audit
        audit = get_self_audit()
        audits = audit.get_recent_audits(limit=200)
        gross_profit = sum(a["actual_r"] for a in audits if a.get("actual_r", 0) > 0)
        gross_loss = abs(sum(a["actual_r"] for a in audits if a.get("actual_r", 0) < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        report["profit_factor"] = round(profit_factor, 2)
    except Exception:
        report["profit_factor"] = 0

    # ── 3. Drawdown ───────────────────────────────────────────────
    try:
        from app.services import risk_governor
        risk = risk_governor.get_risk_status()
        report["drawdown"] = {
            "current_pct": risk.get("drawdown", {}).get("current", 0),
            "max_limit_pct": risk.get("drawdown", {}).get("max_limit", 0),
            "equity": risk.get("equity", {}).get("current", 0),
            "peak_equity": risk.get("equity", {}).get("peak", 0),
        }
    except Exception as e:
        report["drawdown"] = {"error": str(e)}

    # ── 4. Best/Worst Assets ──────────────────────────────────────
    try:
        from app.services.performance_memory import get_performance_memory
        memory = get_performance_memory()
        profiles = memory.get_all_profiles()

        if profiles:
            sorted_by_pnl = sorted(
                profiles.items(),
                key=lambda x: x[1].get("total_pnl", 0),
                reverse=True,
            )
            report["best_assets"] = [
                {"symbol": sym, "pnl": data.get("total_pnl", 0),
                 "win_rate": data.get("win_rate", 0),
                 "trades": data.get("total_trades", 0)}
                for sym, data in sorted_by_pnl[:3] if data.get("total_pnl", 0) > 0
            ]
            report["worst_assets"] = [
                {"symbol": sym, "pnl": data.get("total_pnl", 0),
                 "win_rate": data.get("win_rate", 0),
                 "trades": data.get("total_trades", 0)}
                for sym, data in reversed(sorted_by_pnl[-3:]) if data.get("total_pnl", 0) < 0
            ]
        else:
            report["best_assets"] = []
            report["worst_assets"] = []
    except Exception:
        report["best_assets"] = []
        report["worst_assets"] = []

    # ── 5. Capital Tier Summary ───────────────────────────────────
    try:
        from app.services.capital_tiers import get_tier_engine
        tier = get_tier_engine()
        report["capital_tier"] = {
            "current_tier": tier.get_current_tier().value,
            "context": tier.get_tier_context_for_ai(),
        }
    except Exception:
        report["capital_tier"] = {"current_tier": "UNKNOWN"}

    # ── 6. Session Performance ────────────────────────────────────
    try:
        from app.services.session_intelligence import get_session_tracker
        tracker = get_session_tracker()
        report["session_performance"] = tracker.get_performance()
    except Exception:
        report["session_performance"] = {}

    # ── 7. System Health ──────────────────────────────────────────
    try:
        from app.services.system_health import get_health_guard
        health = get_health_guard()
        report["system_health"] = health.get_latest_report() or {"status": "NO_DATA"}
    except Exception:
        report["system_health"] = {"status": "UNAVAILABLE"}

    logger.info(f"Weekly intelligence report generated for {week_start} to {week_end}")
    return report


def format_report_for_telegram(report: Dict[str, Any]) -> str:
    """Format the weekly report for Telegram delivery."""
    lines = [
        f"<b>NEXUS WEEKLY INTELLIGENCE REPORT</b>",
        f"<i>{report.get('period', {}).get('start', '')} to "
        f"{report.get('period', {}).get('end', '')}</i>",
        "",
    ]

    # Performance
    perf = report.get("performance", {})
    if "error" not in perf:
        lines.extend([
            "<b>PERFORMANCE</b>",
            f"  Trades: {perf.get('total_trades', 0)}",
            f"  Win Rate: {perf.get('win_rate', 0):.1f}%",
            f"  Net P&L: {perf.get('net_pnl_r', 0):+.2f}R",
            f"  Profit Factor: {report.get('profit_factor', 0):.2f}",
            f"  Risk Efficiency: {perf.get('risk_efficiency', 0):.2f}",
            "",
        ])

    # Drawdown
    dd = report.get("drawdown", {})
    if "error" not in dd:
        lines.extend([
            "<b>RISK</b>",
            f"  Drawdown: {dd.get('current_pct', 0):.2f}%",
            f"  Equity: ${dd.get('equity', 0):,.2f}",
            f"  Peak: ${dd.get('peak_equity', 0):,.2f}",
            "",
        ])

    # Best/Worst
    best = report.get("best_assets", [])
    worst = report.get("worst_assets", [])
    if best:
        lines.append("<b>BEST ASSETS</b>")
        for a in best:
            lines.append(f"  {a['symbol']}: ${a['pnl']:+,.2f} ({a['win_rate']:.0f}% WR)")
        lines.append("")
    if worst:
        lines.append("<b>WORST ASSETS</b>")
        for a in worst:
            lines.append(f"  {a['symbol']}: ${a['pnl']:+,.2f} ({a['win_rate']:.0f}% WR)")
        lines.append("")

    # Regime performance
    regimes = report.get("strategy_by_regime", {})
    if regimes:
        lines.append("<b>BY REGIME</b>")
        for regime, data in regimes.items():
            lines.append(
                f"  {regime}: {data.get('trades', 0)} trades, "
                f"{data.get('win_rate', 0):.0f}% WR"
            )
        lines.append("")

    # Tier
    tier = report.get("capital_tier", {})
    lines.append(f"<b>CAPITAL TIER:</b> {tier.get('current_tier', 'UNKNOWN')}")

    # Avoid
    avoid = report.get("assets_to_avoid", [])
    if avoid:
        lines.append(f"<b>ASSETS TO AVOID:</b> {', '.join(avoid)}")

    return "\n".join(lines)
