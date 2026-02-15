"""
NEXUS Command Router — Intent → Engine Routing
================================================

Routes validated intents to the correct engine:
- trade_request → Risk Governor (NEVER execution directly)
- trade_suggestion → Intelligence analysis
- analysis → Market data / regime detection
- system_query → Health / status / risk summary

ARCHITECTURE LAW:
This module NEVER imports execution.py.
All trade intents pass through risk validation.
"""

import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger("nexus.router")


@dataclass
class RouteResult:
    """Result from routing an intent."""
    success: bool
    route: str          # Which engine handled this
    action_taken: str   # What was done
    data: Dict[str, Any]
    requires_user_action: bool = False
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CommandRouter:
    """
    Routes validated intents to appropriate engines.
    
    NEVER calls execution directly.
    Trade intents → risk validation → returns approval/rejection.
    """

    def __init__(self):
        self._initialized = True

    async def route(
        self,
        intent_data: Dict[str, Any],
        user_id: str = "unknown"
    ) -> RouteResult:
        """
        Route a validated intent to the correct engine.
        
        Args:
            intent_data: TradeIntent.to_dict() output
            user_id: For logging
        
        Returns:
            RouteResult with engine response
        """
        intent_type = intent_data.get("intent", "unknown")
        
        logger.info(f"Routing intent: {intent_type} from {user_id[:8]}...")

        if intent_type == "trade_request":
            return await self._route_trade_request(intent_data)

        elif intent_type == "trade_suggestion":
            return await self._route_trade_suggestion(intent_data)

        elif intent_type == "analysis":
            return await self._route_analysis(intent_data)

        elif intent_type == "system_query":
            return await self._route_system_query(intent_data)

        elif intent_type == "clarification_needed":
            return RouteResult(
                success=True,
                route="CLARIFICATION",
                action_taken="AWAITING_USER_INPUT",
                data=intent_data,
                requires_user_action=True,
                message=intent_data.get("reasoning", "Please clarify your command.")
            )

        elif intent_type == "error":
            return RouteResult(
                success=False,
                route="ERROR",
                action_taken="PARSE_FAILED",
                data=intent_data,
                requires_user_action=True,
                message=intent_data.get("error", "Failed to understand command.")
            )

        else:
            return RouteResult(
                success=False,
                route="UNKNOWN",
                action_taken="UNRECOGNIZED_INTENT",
                data={"intent": intent_type},
                requires_user_action=True,
                message=f"Unknown intent type: {intent_type}"
            )

    # =========================================================================
    # TRADE REQUEST → RISK GOVERNOR
    # =========================================================================
    async def _route_trade_request(self, intent_data: Dict[str, Any]) -> RouteResult:
        """
        Route trade request through risk validation.
        
        Does NOT execute. Returns risk approval for caller to act on.
        """
        try:
            from app.services import risk_governor

            asset = intent_data.get("asset", "UNKNOWN")
            direction = intent_data.get("direction", "none")
            lot_size = intent_data.get("lot_size", 0.01)
            confidence = intent_data.get("confidence", 0.0)

            # Use lot_size default if None
            if lot_size is None:
                return RouteResult(
                    success=True,
                    route="RISK_GATE",
                    action_taken="AWAITING_LOT_SIZE",
                    data={
                        "asset": asset,
                        "direction": direction,
                        "status": "NEEDS_LOT_SIZE"
                    },
                    requires_user_action=True,
                    message=f"Trade {direction.upper()} {asset} received. Please specify lot size."
                )

            # Run risk validation
            risk_ok, risk_msg = risk_governor.validate_trade(
                symbol=asset,
                quantity=float(lot_size),
                price=0.0,  # Price will be determined at execution
                strategy_confidence=confidence
            )

            if risk_ok:
                return RouteResult(
                    success=True,
                    route="RISK_GATE",
                    action_taken="RISK_APPROVED",
                    data={
                        "asset": asset,
                        "direction": direction,
                        "lot_size": lot_size,
                        "stop_loss": intent_data.get("stop_loss"),
                        "take_profit": intent_data.get("take_profit"),
                        "risk_status": "APPROVED",
                        "risk_message": risk_msg
                    },
                    requires_user_action=intent_data.get("requires_confirmation", True),
                    message=f"Risk APPROVED: {direction.upper()} {lot_size} {asset}. {risk_msg}"
                )
            else:
                return RouteResult(
                    success=False,
                    route="RISK_GATE",
                    action_taken="RISK_REJECTED",
                    data={
                        "asset": asset,
                        "direction": direction,
                        "lot_size": lot_size,
                        "risk_status": "REJECTED",
                        "risk_message": risk_msg
                    },
                    requires_user_action=False,
                    message=f"Risk REJECTED: {risk_msg}"
                )

        except Exception as e:
            logger.error(f"Trade routing error: {e}")
            return RouteResult(
                success=False,
                route="RISK_GATE",
                action_taken="ROUTING_ERROR",
                data={"error": str(e)},
                message=f"Failed to validate trade: {e}"
            )

    # =========================================================================
    # TRADE SUGGESTION → INTELLIGENCE
    # =========================================================================
    async def _route_trade_suggestion(self, intent_data: Dict[str, Any]) -> RouteResult:
        """Route trade suggestion to intelligence for analysis."""
        try:
            from app.services import intelligence

            asset = intent_data.get("asset", "BTCUSD")
            direction = intent_data.get("direction", "none")

            # Get market analysis
            analysis = intelligence.analyze_market({
                "symbol": asset,
                "suggested_direction": direction,
                "source": "user_suggestion"
            })

            return RouteResult(
                success=True,
                route="INTELLIGENCE",
                action_taken="ANALYSIS_COMPLETE",
                data={
                    "asset": asset,
                    "user_suggestion": direction,
                    "ai_signal": analysis.get("signal", "WAIT"),
                    "ai_confidence": analysis.get("confidence", 0.0),
                    "ai_regime": analysis.get("regime", "UNCERTAIN"),
                    "ai_risk_level": analysis.get("risk_level", "MEDIUM"),
                    "reasoning": analysis.get("reasoning", "")
                },
                message=f"Analysis for {asset}: Signal={analysis.get('signal', 'WAIT')}, "
                        f"Confidence={analysis.get('confidence', 0):.0%}"
            )

        except Exception as e:
            logger.error(f"Suggestion routing error: {e}")
            return RouteResult(
                success=False,
                route="INTELLIGENCE",
                action_taken="ANALYSIS_FAILED",
                data={"error": str(e)},
                message=f"Analysis failed: {e}"
            )

    # =========================================================================
    # ANALYSIS → MARKET DATA
    # =========================================================================
    async def _route_analysis(self, intent_data: Dict[str, Any]) -> RouteResult:
        """Route analysis query to intelligence engine."""
        try:
            from app.services import intelligence

            asset = intent_data.get("asset")
            reasoning = intent_data.get("reasoning", "")

            if asset:
                analysis = intelligence.analyze_market({
                    "symbol": asset,
                    "query": reasoning,
                    "source": "user_query"
                })

                return RouteResult(
                    success=True,
                    route="INTELLIGENCE",
                    action_taken="MARKET_ANALYSIS",
                    data={
                        "asset": asset,
                        "signal": analysis.get("signal", "WAIT"),
                        "regime": analysis.get("regime", "UNCERTAIN"),
                        "confidence": analysis.get("confidence", 0.0),
                        "risk_level": analysis.get("risk_level", "MEDIUM"),
                        "reasoning": analysis.get("reasoning", "No detailed analysis available")
                    },
                    message=f"{asset} regime: {analysis.get('regime', 'UNCERTAIN')}, "
                            f"risk: {analysis.get('risk_level', 'MEDIUM')}"
                )
            else:
                return RouteResult(
                    success=True,
                    route="INTELLIGENCE",
                    action_taken="GENERAL_ANALYSIS",
                    data={"query": reasoning},
                    requires_user_action=True,
                    message="Please specify an asset for analysis. Example: 'Analyze XAUUSD'"
                )

        except Exception as e:
            logger.error(f"Analysis routing error: {e}")
            return RouteResult(
                success=False,
                route="INTELLIGENCE",
                action_taken="ANALYSIS_FAILED",
                data={"error": str(e)},
                message=f"Analysis failed: {e}"
            )

    # =========================================================================
    # SYSTEM QUERY → HEALTH/STATUS
    # =========================================================================
    async def _route_system_query(self, intent_data: Dict[str, Any]) -> RouteResult:
        """Route system query to health/status engines."""
        try:
            from app.services import risk_governor
            from app.services.circuit_breaker import get_manager

            cb = get_manager()
            trading_allowed, reason = cb.is_trading_allowed()
            risk_status = risk_governor.get_risk_status()

            return RouteResult(
                success=True,
                route="SYSTEM",
                action_taken="STATUS_REPORT",
                data={
                    "system": "ONLINE",
                    "trading_allowed": trading_allowed,
                    "trading_reason": reason,
                    "risk": {
                        "drawdown": risk_status.get("drawdown", {}),
                        "equity": risk_status.get("equity", {}),
                        "positions": risk_status.get("positions", {})
                    },
                    "circuit_breakers": cb.get_all_status(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                message=f"NEXUS ONLINE. Trading: {'ENABLED' if trading_allowed else 'DISABLED'}. "
                        f"{reason}"
            )

        except Exception as e:
            logger.error(f"System query routing error: {e}")
            return RouteResult(
                success=True,
                route="SYSTEM",
                action_taken="PARTIAL_STATUS",
                data={"system": "ONLINE", "error": str(e)},
                message=f"NEXUS ONLINE. Some subsystems unavailable: {str(e)[:50]}"
            )


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================
_router: Optional[CommandRouter] = None


def get_router() -> CommandRouter:
    """Get or create global CommandRouter instance."""
    global _router
    if _router is None:
        _router = CommandRouter()
    return _router
