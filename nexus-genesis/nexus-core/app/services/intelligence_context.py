"""
NEXUS Intelligence Context Builder — Phase 5, Part E + Integration
====================================================================

Builds rich market context for AI prompts by composing:
  - Market regime (Part A)
  - Multi-timeframe confluence (Part B)
  - News awareness (Part C)
  - Performance memory (Part D)
  - Risk state summary

Also defines the institutional conversational tone and response
formatting rules.

AI MUST:
  - Reference regime in every explanation
  - Reference risk state
  - Reference confidence level
  - Speak like a calm institutional trader (no emojis, no hype)

AI MUST NEVER:
  - Execute trades from conversation
  - Assume intent
  - Act without structured approval
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("nexus.intelligence_context")


# =============================================================================
# INSTITUTIONAL SYSTEM PROMPT
# =============================================================================

INSTITUTIONAL_SYSTEM_PROMPT = """You are NEXUS, an institutional-grade trading intelligence system.

COMMUNICATION STYLE:
- Speak like a senior portfolio manager at a systematic hedge fund.
- Be calm, precise, and data-driven. No hype. No speculation.
- Never use emojis, slang, or exclamation marks.
- Reference specific data points: regime, confidence, risk metrics.
- When uncertain, say so directly. Never fabricate certainty.

RESPONSE STRUCTURE:
Every response must include:
1. Current market regime for the referenced asset
2. Current risk state (equity, drawdown, daily P&L)
3. Confidence level for any assessment
4. Clear reasoning backed by observable data

ABSOLUTE RULES:
- You NEVER execute trades. You only analyze and suggest.
- You NEVER assume the user wants to trade.
- You NEVER bypass risk limits or capital protection rules.
- If asked "should I buy X?", provide analysis, not a command.
- All trade actions require structured JSON intent submission.
- Say "I recommend reviewing..." not "Buy now" or "Go long".

EXAMPLE RESPONSES:
Q: "What's the market doing?"
A: "EURUSD is in a RANGE_BOUND regime with ATR at the 32nd percentile.
   Momentum persistence is low at 1 bar. No high-impact events are
   scheduled within the next 4 hours. Current equity drawdown is 0.4%,
   well within limits. I see no high-conviction setups at this time."

Q: "Any good setups today?"
A: "XAUUSD shows TRENDING regime with 4-bar momentum persistence and
   bullish alignment across H4 and H1 timeframes. Confluence score
   is 78%. Historical win rate for gold in trending regimes is 62%.
   Risk per trade would be 1.0% of equity. If you want to proceed,
   submit a structured trade intent for review."

Q: "Why did you avoid gold?"
A: "Gold was in a HIGH_VOLATILITY regime with ATR at the 89th percentile
   and expanding. The news filter flagged an upcoming FOMC decision
   within 45 minutes. Per risk protocol, new entries are blocked during
   high-impact news windows. This is a capital preservation measure."
"""


# =============================================================================
# CONTEXT BUILDER
# =============================================================================

def build_intelligence_context(
    symbol: str,
    market_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a comprehensive intelligence context string for AI prompt injection.

    Composes:
      1. Market regime context
      2. News awareness context
      3. Performance memory context
      4. Risk state summary

    Returns a formatted multi-line string for LLM consumption.
    """
    sections = []

    # ── 1. Market Regime ──────────────────────────────────────────
    try:
        from app.services.market_regime import get_regime_store
        regime_store = get_regime_store()
        regime_ctx = regime_store.get_regime_context_for_ai(symbol)
        sections.append(regime_ctx)

        # Get regime name for performance memory
        regime_state = regime_store.get(symbol)
        current_regime = regime_state.regime.value if regime_state else "UNKNOWN"
    except Exception:
        sections.append(f"REGIME: Data unavailable for {symbol}.")
        current_regime = "UNKNOWN"

    # ── 2. News Awareness ─────────────────────────────────────────
    try:
        from app.services.news_awareness import get_news_calendar
        calendar = get_news_calendar()
        news_ctx = calendar.get_news_context_for_ai(symbol)
        sections.append(news_ctx)
    except Exception:
        sections.append(f"NEWS STATUS FOR {symbol}: Calendar unavailable.")

    # ── 3. Performance Memory ─────────────────────────────────────
    try:
        from app.services.performance_memory import get_performance_memory
        memory = get_performance_memory()
        perf_ctx = memory.get_performance_context_for_ai(symbol, current_regime)
        sections.append(perf_ctx)
    except Exception:
        sections.append(f"PERFORMANCE MEMORY FOR {symbol}: No data available.")

    # ── 4. Risk State ─────────────────────────────────────────────
    try:
        from app.services import risk_governor
        risk = risk_governor.get_risk_status()
        risk_lines = [
            "CURRENT RISK STATE:",
            f"  Risk Level: {risk.get('risk_level', 'UNKNOWN')}",
            f"  Trading Enabled: {risk.get('trading_enabled', False)}",
            f"  Equity: ${risk.get('equity', {}).get('current', 0):,.2f}",
            f"  Drawdown: {risk.get('drawdown', {}).get('current', 0):.2f}%",
            f"  Open Positions: {risk.get('open_positions_count', 0)}",
            f"  Consecutive Losses: {risk.get('consecutive_losses', 0)}",
        ]
        sections.append("\n".join(risk_lines))
    except Exception:
        sections.append("RISK STATE: Unavailable.")

    # ── 5. Daily P&L ──────────────────────────────────────────────
    try:
        from app.services.capital_protection import get_daily_tracker
        daily = get_daily_tracker().get_daily_summary()
        daily_lines = [
            "DAILY PERFORMANCE:",
            f"  P&L: {daily.get('daily_pnl_pct', 0):+.2f}%"
            f" (${daily.get('daily_pnl', 0):+,.2f})",
            f"  Trades Today: {daily.get('trades_today', 0)}"
            f" (W:{daily.get('wins', 0)} / L:{daily.get('losses', 0)})",
            f"  Daily Cap Hit: {daily.get('cap_hit', False)}",
        ]
        sections.append("\n".join(daily_lines))
    except Exception:
        sections.append("DAILY PERFORMANCE: Unavailable.")

    return "\n\n".join(sections)


def build_full_ai_prompt(
    symbol: str,
    user_message: str,
    market_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a complete AI prompt with system instructions + market context.

    For use with the LLM conversation layer.
    """
    context = build_intelligence_context(symbol, market_data)

    prompt = (
        f"{INSTITUTIONAL_SYSTEM_PROMPT}\n\n"
        f"--- MARKET INTELLIGENCE ---\n"
        f"{context}\n\n"
        f"--- USER QUERY ---\n"
        f"{user_message}"
    )

    return prompt


def build_trade_analysis_context(
    symbol: str,
    side: str,
    market_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a structured context dict for trade decision analysis.

    Used by the AI decision engine to enrich trade intents with
    regime awareness, confluence data, and performance memory.
    """
    context: Dict[str, Any] = {
        "symbol": symbol,
        "side": side,
    }

    # Regime
    try:
        from app.services.market_regime import get_regime_store, Regime
        regime_store = get_regime_store()
        regime_state = regime_store.get(symbol)
        if regime_state:
            context["regime"] = regime_state.to_dict()
            context["has_regime"] = regime_state.regime != Regime.UNKNOWN
        else:
            context["regime"] = None
            context["has_regime"] = False
    except Exception:
        context["regime"] = None
        context["has_regime"] = False

    # News blackout
    try:
        from app.services.news_awareness import get_news_calendar
        calendar = get_news_calendar()
        in_blackout, event = calendar.is_in_blackout_window(symbol)
        context["news_blackout"] = in_blackout
        context["news_event"] = event.to_dict() if event else None
    except Exception:
        context["news_blackout"] = False
        context["news_event"] = None

    # Performance memory confidence adjustment
    try:
        from app.services.performance_memory import get_performance_memory
        memory = get_performance_memory()
        regime_name = context.get("regime", {})
        if isinstance(regime_name, dict):
            regime_name = regime_name.get("regime", "UNKNOWN")
        else:
            regime_name = "UNKNOWN"
        context["confidence_adjustment"] = memory.get_confidence_adjustment(symbol, regime_name)
        context["frequency_hint"] = memory.get_frequency_hint(symbol)
    except Exception:
        context["confidence_adjustment"] = 1.0
        context["frequency_hint"] = "NORMAL"

    return context
