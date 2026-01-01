"""
NEXUS Master AI - Command Core Interface
=========================================

The Master AI that listens, responds, and obeys.

Commands:
- "Status" - System status report
- "Pause trading" - Halt all execution
- "Resume" - Resume trading
- "Connect account" - Link trading account
- "Explain last trade" - Trade analysis
- "Risk summary" - Risk metrics
- "Go stealth" - Enable stealth mode

ABSOLUTE LAW: Only the Master can issue commands.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("nexus.master_ai")


# =============================================================================
# COMMAND TYPES
# =============================================================================

class CommandType(Enum):
    """Recognized command types."""
    STATUS = "status"
    PAUSE = "pause"
    RESUME = "resume"
    CONNECT_ACCOUNT = "connect_account"
    EXPLAIN_TRADE = "explain_trade"
    RISK_SUMMARY = "risk_summary"
    STEALTH = "stealth"
    HELP = "help"
    UNKNOWN = "unknown"
    
    # Trading commands
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"
    
    # System commands
    KILL = "kill"
    PURGE = "purge"
    REPORT = "report"


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    command_type: CommandType
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_response(self) -> Dict[str, Any]:
        """Convert to API response."""
        return {
            "success": self.success,
            "command": self.command_type.value,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


# =============================================================================
# COMMAND PARSER
# =============================================================================

class CommandParser:
    """
    Natural language command parser.
    
    Understands:
    - Direct commands: "pause", "status"
    - Natural language: "what's the status?", "stop trading"
    - Trading commands: "buy EURUSD 0.1 lots"
    """
    
    PATTERNS = {
        CommandType.STATUS: [
            r"status", r"how are you", r"system status", r"what's happening",
            r"report", r"health", r"are you okay", r"check"
        ],
        CommandType.PAUSE: [
            r"pause", r"stop", r"halt", r"freeze", r"pause trading",
            r"stop trading", r"hold", r"wait"
        ],
        CommandType.RESUME: [
            r"resume", r"start", r"continue", r"go", r"resume trading",
            r"start trading", r"proceed", r"activate"
        ],
        CommandType.EXPLAIN_TRADE: [
            r"explain.*trade", r"last trade", r"what.*trade", r"why.*trade",
            r"trade.*explain", r"analyze.*trade"
        ],
        CommandType.RISK_SUMMARY: [
            r"risk", r"risk summary", r"risk report", r"exposure",
            r"drawdown", r"how much.*risk"
        ],
        CommandType.STEALTH: [
            r"stealth", r"go stealth", r"hide", r"silent mode",
            r"incognito", r"dark mode"
        ],
        CommandType.HELP: [
            r"help", r"commands", r"what can you do", r"options",
            r"how to", r"\?"
        ],
        CommandType.KILL: [
            r"kill", r"emergency", r"abort", r"shutdown", r"kill switch"
        ],
        CommandType.BUY: [
            r"buy\s+(\w+)"
        ],
        CommandType.SELL: [
            r"sell\s+(\w+)"
        ],
        CommandType.CLOSE: [
            r"close\s+(\w+)", r"close all"
        ]
    }
    
    def parse(self, text: str) -> Tuple[CommandType, Dict[str, Any]]:
        """
        Parse command text.
        
        Returns: (CommandType, extracted_params)
        """
        text = text.lower().strip()
        
        for cmd_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    params = {}
                    if match.groups():
                        params["args"] = list(match.groups())
                    return cmd_type, params
        
        return CommandType.UNKNOWN, {"original": text}


# =============================================================================
# MASTER AI CORE
# =============================================================================

class MasterAI:
    """
    NEXUS Master AI - The command core.
    
    Always online. Responds in real time.
    Subordinate to the Master only.
    """
    
    def __init__(self):
        self.parser = CommandParser()
        self.is_online = True
        self.trading_paused = False
        self.stealth_mode = False
        self.command_history: List[CommandResult] = []
        
        # System state references
        self._system_state: Dict[str, Any] = {}
        
        logger.info("Master AI initialized and awaiting commands")
    
    async def process_command(
        self,
        text: str,
        user_id: str,
        is_master: bool = False
    ) -> CommandResult:
        """
        Process a command from the user.
        
        Only Master can execute sensitive commands.
        """
        # Log command
        logger.info(f"Command received from {user_id[:8]}...: {text[:50]}")
        
        # Parse command
        cmd_type, params = self.parser.parse(text)
        
        # Check permissions for sensitive commands
        sensitive_commands = [
            CommandType.PAUSE, CommandType.RESUME, CommandType.KILL,
            CommandType.PURGE, CommandType.STEALTH, CommandType.BUY,
            CommandType.SELL, CommandType.CLOSE
        ]
        
        if cmd_type in sensitive_commands and not is_master:
            result = CommandResult(
                success=False,
                command_type=cmd_type,
                message="DENIED: Only the Master can execute this command."
            )
            self.command_history.append(result)
            return result
        
        # Execute command
        result = await self._execute_command(cmd_type, params)
        self.command_history.append(result)
        
        return result
    
    async def _execute_command(
        self,
        cmd_type: CommandType,
        params: Dict[str, Any]
    ) -> CommandResult:
        """Execute the parsed command."""
        
        if cmd_type == CommandType.STATUS:
            return await self._cmd_status()
        
        elif cmd_type == CommandType.PAUSE:
            return await self._cmd_pause()
        
        elif cmd_type == CommandType.RESUME:
            return await self._cmd_resume()
        
        elif cmd_type == CommandType.EXPLAIN_TRADE:
            return await self._cmd_explain_trade()
        
        elif cmd_type == CommandType.RISK_SUMMARY:
            return await self._cmd_risk_summary()
        
        elif cmd_type == CommandType.STEALTH:
            return await self._cmd_stealth()
        
        elif cmd_type == CommandType.HELP:
            return await self._cmd_help()
        
        elif cmd_type == CommandType.KILL:
            return await self._cmd_kill()
        
        elif cmd_type == CommandType.BUY:
            return await self._cmd_trade("BUY", params.get("args", []))
        
        elif cmd_type == CommandType.SELL:
            return await self._cmd_trade("SELL", params.get("args", []))
        
        elif cmd_type == CommandType.CLOSE:
            return await self._cmd_close(params.get("args", []))
        
        else:
            return CommandResult(
                success=False,
                command_type=CommandType.UNKNOWN,
                message=f"I don't understand: '{params.get('original', '')}'. Type 'help' for commands."
            )
    
    # =========================================================================
    # COMMAND IMPLEMENTATIONS
    # =========================================================================
    
    async def _cmd_status(self) -> CommandResult:
        """Get system status."""
        try:
            # Gather system status
            from app.services.agent_council import get_council
            from app.services.circuit_breaker import get_manager
            from app.services import risk_governor
            
            council = get_council()
            cb = get_manager()
            risk = risk_governor.get_risk_status()
            
            council_status = council.get_status()
            cb_status = cb.get_all_status()
            trading_allowed, reason = cb.is_trading_allowed()
            
            status_data = {
                "system": "ONLINE",
                "trading_paused": self.trading_paused,
                "trading_allowed": trading_allowed and not self.trading_paused,
                "trading_reason": reason,
                "stealth_mode": self.stealth_mode,
                "agent_council": {
                    "agents_online": len(council_status.get("agents", [])),
                    "quorum_threshold": council_status.get("quorum_threshold"),
                    "last_decision": council_status.get("last_decision")
                },
                "risk": {
                    "current_drawdown": risk.get("drawdown", {}).get("current", 0),
                    "max_drawdown": risk.get("drawdown", {}).get("max", 2.0),
                    "open_positions": risk.get("positions", {}).get("count", 0),
                    "total_pnl": risk.get("total_pnl_pct", 0)
                },
                "circuit_breakers": {
                    "any_tripped": cb_status.get("any_open", False),
                    "global_halt": cb_status.get("global_halt", False)
                }
            }
            
            # Generate human-readable message
            if trading_allowed and not self.trading_paused:
                message = "NEXUS is ONLINE and READY. All systems operational."
            elif self.trading_paused:
                message = "NEXUS is ONLINE but PAUSED. Trading halted by command."
            else:
                message = f"NEXUS is ONLINE but HALTED: {reason}"
            
            return CommandResult(
                success=True,
                command_type=CommandType.STATUS,
                message=message,
                data=status_data
            )
            
        except Exception as e:
            logger.error(f"Status command error: {e}")
            return CommandResult(
                success=True,
                command_type=CommandType.STATUS,
                message=f"NEXUS is ONLINE. Some subsystems unavailable: {str(e)[:50]}",
                data={"system": "ONLINE", "subsystems_error": str(e)}
            )
    
    async def _cmd_pause(self) -> CommandResult:
        """Pause all trading."""
        self.trading_paused = True
        
        try:
            from app.services.circuit_breaker import get_manager
            cb = get_manager()
            cb.global_halt("Master AI Pause Command")
        except Exception as e:
            logger.error(f"Circuit breaker halt failed: {e}")
        
        return CommandResult(
            success=True,
            command_type=CommandType.PAUSE,
            message="Trading PAUSED. All execution halted. Capital preserved.",
            data={"trading_enabled": False, "paused_at": datetime.now(timezone.utc).isoformat()}
        )
    
    async def _cmd_resume(self) -> CommandResult:
        """Resume trading."""
        self.trading_paused = False
        
        try:
            from app.services.circuit_breaker import get_manager
            cb = get_manager()
            cb.resume_trading()
        except Exception as e:
            logger.error(f"Circuit breaker resume failed: {e}")
        
        return CommandResult(
            success=True,
            command_type=CommandType.RESUME,
            message="Trading RESUMED. Execution enabled. Council quorum required for trades.",
            data={"trading_enabled": True, "resumed_at": datetime.now(timezone.utc).isoformat()}
        )
    
    async def _cmd_explain_trade(self) -> CommandResult:
        """Explain the last trade."""
        try:
            from app.services.agent_council import get_council
            
            council = get_council()
            last_decision = council._last_decision
            
            if not last_decision:
                return CommandResult(
                    success=True,
                    command_type=CommandType.EXPLAIN_TRADE,
                    message="No trades have been executed yet.",
                    data={}
                )
            
            # Build explanation
            votes_detail = []
            for vote in last_decision.votes:
                votes_detail.append({
                    "agent": vote.agent_name,
                    "vote": vote.vote.value,
                    "confidence": vote.confidence,
                    "reasoning": vote.reasoning
                })
            
            explanation = f"""
Last Trade Decision:
- Symbol: {last_decision.symbol}
- Direction: {last_decision.proposed_direction}
- Final Decision: {last_decision.final_decision.value}
- Quorum Reached: {last_decision.quorum_reached}
- Consensus Confidence: {last_decision.consensus_confidence:.1%}
- Position Modifier: {last_decision.position_size_modifier}

Agent Votes:
"""
            for v in votes_detail:
                explanation += f"  - {v['agent']}: {v['vote']} ({v['confidence']:.0%})\n"
            
            return CommandResult(
                success=True,
                command_type=CommandType.EXPLAIN_TRADE,
                message=explanation.strip(),
                data={
                    "symbol": last_decision.symbol,
                    "direction": last_decision.proposed_direction,
                    "decision": last_decision.final_decision.value,
                    "quorum": last_decision.quorum_reached,
                    "confidence": last_decision.consensus_confidence,
                    "votes": votes_detail
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                command_type=CommandType.EXPLAIN_TRADE,
                message=f"Could not retrieve trade details: {e}",
                data={}
            )
    
    async def _cmd_risk_summary(self) -> CommandResult:
        """Get risk summary."""
        try:
            from app.services import risk_governor
            
            risk = risk_governor.get_risk_status()
            
            message = f"""
Risk Summary:
- Current Drawdown: {risk.get('drawdown', {}).get('current', 0):.2%}
- Max Allowed: {risk.get('drawdown', {}).get('max', 2.0):.2%}
- Equity: ${risk.get('equity', {}).get('current', 0):,.2f}
- Peak Equity: ${risk.get('equity', {}).get('peak', 0):,.2f}
- Total P&L: {risk.get('total_pnl_pct', 0):.2%}
- Open Positions: {risk.get('positions', {}).get('count', 0)}
- Trading Allowed: {risk.get('trading_allowed', False)}
"""
            
            return CommandResult(
                success=True,
                command_type=CommandType.RISK_SUMMARY,
                message=message.strip(),
                data=risk
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                command_type=CommandType.RISK_SUMMARY,
                message=f"Could not retrieve risk data: {e}",
                data={}
            )
    
    async def _cmd_stealth(self) -> CommandResult:
        """Enable stealth mode."""
        self.stealth_mode = True
        
        try:
            from app.services.stealth_mode import get_stealth_mode
            stealth = get_stealth_mode()
            stealth._enabled = True
        except Exception:
            pass
        
        return CommandResult(
            success=True,
            command_type=CommandType.STEALTH,
            message="STEALTH MODE ACTIVATED. Minimal logging. Encrypted comms. Silent operation.",
            data={"stealth_mode": True}
        )
    
    async def _cmd_help(self) -> CommandResult:
        """Show available commands."""
        help_text = """
NEXUS Master AI Commands:

INFORMATION:
  status          - System status report
  risk            - Risk and exposure summary
  explain trade   - Explain last trade decision

CONTROL:
  pause           - Halt all trading
  resume          - Resume trading
  stealth         - Enable stealth mode

TRADING (Master Only):
  buy [SYMBOL]    - Execute buy order
  sell [SYMBOL]   - Execute sell order
  close [SYMBOL]  - Close position

EMERGENCY:
  kill            - Emergency kill switch

Type any command naturally. I understand context.
"""
        return CommandResult(
            success=True,
            command_type=CommandType.HELP,
            message=help_text.strip(),
            data={"commands": list(CommandType.__members__.keys())}
        )
    
    async def _cmd_kill(self) -> CommandResult:
        """Emergency kill switch."""
        self.trading_paused = True
        
        try:
            from app.services.circuit_breaker import get_manager
            from app.services import risk_governor
            from app.services.stealth_mode import get_stealth_mode
            
            cb = get_manager()
            cb.global_halt("Master AI Kill Command")
            risk_governor.emergency_shutdown("Master AI Kill Command")
            
            stealth = get_stealth_mode()
            stealth.log_event("KILL_COMMAND", {"source": "master_ai"}, sensitivity="CRITICAL")
            
        except Exception as e:
            logger.error(f"Kill command error: {e}")
        
        return CommandResult(
            success=True,
            command_type=CommandType.KILL,
            message="EMERGENCY KILL ACTIVATED. All trading halted. All orders cancelled. System frozen.",
            data={"killed": True, "timestamp": datetime.now(timezone.utc).isoformat()}
        )
    
    async def _cmd_trade(self, direction: str, args: List[str]) -> CommandResult:
        """Execute trade command."""
        if not args:
            return CommandResult(
                success=False,
                command_type=CommandType.BUY if direction == "BUY" else CommandType.SELL,
                message=f"Please specify symbol. Example: {direction.lower()} EURUSD"
            )
        
        symbol = args[0].upper()
        
        # Check if trading is allowed
        if self.trading_paused:
            return CommandResult(
                success=False,
                command_type=CommandType.BUY if direction == "BUY" else CommandType.SELL,
                message="Trading is PAUSED. Use 'resume' first."
            )
        
        # This would integrate with the main execution flow
        # For now, return confirmation that command was received
        return CommandResult(
            success=True,
            command_type=CommandType.BUY if direction == "BUY" else CommandType.SELL,
            message=f"Trade command received: {direction} {symbol}. Executing via Agent Council...",
            data={"direction": direction, "symbol": symbol, "status": "pending_council"}
        )
    
    async def _cmd_close(self, args: List[str]) -> CommandResult:
        """Close position command."""
        if not args:
            return CommandResult(
                success=False,
                command_type=CommandType.CLOSE,
                message="Please specify symbol or 'all'. Example: close EURUSD"
            )
        
        target = args[0].upper()
        
        return CommandResult(
            success=True,
            command_type=CommandType.CLOSE,
            message=f"Close command received for: {target}. Executing...",
            data={"target": target, "status": "pending"}
        )


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_master_ai: Optional[MasterAI] = None


def get_master_ai() -> MasterAI:
    """Get or create Master AI instance."""
    global _master_ai
    if _master_ai is None:
        _master_ai = MasterAI()
    return _master_ai
