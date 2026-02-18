"""
NEXUS Telegram Bot Service — Production Hardened
==================================================

Provides real-time interaction with the trading bot via Telegram.

Features:
1. Command handling (/start, /status, /analyze, /signal)
2. Emergency controls (/halt, /resume, /close_all)
3. Hardening integration (whitelist, rate limit, confirmation)
4. Asynchronous integration with FastAPI
5. Secure token management
6. Execution log mirroring
"""

import logging
import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# Local service imports
from app.services.intelligence import NexusIntelligence, MarketRegime
from app.services.model_ensemble import get_ensemble, Prediction

logger = logging.getLogger("nexus.telegram")


class TelegramService:
    """
    Manages the Telegram Bot lifecycle and command handling.

    Integrates with Phase 11 hardening for:
    - Whitelist-only access
    - Rate limiting
    - High-risk command confirmation
    - Full audit logging
    """

    def __init__(self):
        self.output_queue = asyncio.Queue()
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.allowed_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.application: Optional[Application] = None
        self.bot_info: Optional[Any] = None
        self.is_running = False

        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Bot service disabled.")
            return

        # Initialize Intelligence for on-demand analysis
        self.intelligence = NexusIntelligence()

    async def start(self):
        """Initialize and start the bot."""
        if not self.token:
            return

        try:
            # Build application
            builder = Application.builder().token(self.token)
            self.application = builder.build()

            # Core commands
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("analyze", self.cmd_analyze))
            self.application.add_handler(CommandHandler("signal", self.cmd_signal))
            self.application.add_handler(CommandHandler("help", self.cmd_help))

            # Emergency commands (Phase C)
            self.application.add_handler(CommandHandler("halt", self.cmd_halt))
            self.application.add_handler(CommandHandler("resume", self.cmd_resume))
            self.application.add_handler(CommandHandler("close_all", self.cmd_close_all))

            # Initialize and start
            await self.application.initialize()
            await self.application.start()

            asyncio.create_task(self._run_polling())

            self.bot_info = await self.application.bot.get_me()
            self.is_running = True
            logger.info(f"Telegram Bot started: @{self.bot_info.username}")

            # Send startup message if chat ID is known
            if self.allowed_chat_id:
                await self.send_message("NEXUS AI Trading Bot Online")

        except Exception as e:
            logger.error(f"Failed to start Telegram Bot: {e}")

    async def _run_polling(self):
        """Run bot polling in background."""
        if not self.application:
            return

        try:
            await self.application.updater.start_polling()
            logger.info("Telegram polling started")
        except Exception as e:
            logger.error(f"Polling error: {e}")

    async def stop(self):
        """Stop the bot."""
        if self.application:
            try:
                if self.allowed_chat_id:
                    await self.send_message("NEXUS AI System Shutdown")

                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                self.is_running = False
                logger.info("Telegram Bot stopped")
            except Exception as e:
                logger.error(f"Error stopping Telegram Bot: {e}")

    async def send_message(self, text: str):
        """Send a message to the allowed chat ID."""
        if not self.application or not self.allowed_chat_id:
            return

        try:
            await self.application.bot.send_message(
                chat_id=self.allowed_chat_id, text=text, parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    # =========================================================================
    # AUTH CHECK (integrated with Phase 11 hardening)
    # =========================================================================

    async def _check_auth(self, update: Update, command: str = "") -> bool:
        """
        Check if user is authorized.

        Uses Phase 11 TelegramHardening when available for:
        - Whitelist enforcement
        - Rate limiting
        - High-risk command confirmation flow
        """
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        username = update.effective_user.username or ""

        # Try hardening layer first
        try:
            from security.telegram_hardening import get_telegram_hardening
            hardening = get_telegram_hardening()
            allowed, reason = hardening.validate_command(
                chat_id=chat_id,
                user_id=user_id,
                command=command or update.message.text or "",
                username=username,
            )
            if not allowed:
                await update.message.reply_text(reason)
                return False
            return True
        except ImportError:
            pass

        # Fallback: simple chat ID check
        if self.allowed_chat_id and user_id != str(self.allowed_chat_id):
            await update.message.reply_text("Unauthorized access.")
            logger.warning(f"Unauthorized access attempt from ID: {user_id}")
            return False
        return True

    # =========================================================================
    # CORE COMMAND HANDLERS
    # =========================================================================

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        if not await self._check_auth(update, "/start"):
            return

        welcome_msg = (
            "*NEXUS AI Operational*\n\n"
            "Systems nominal. Ready for command.\n\n"
            "*Core Commands:*\n"
            "/status - Full System Status\n"
            "/signal - Current Signal\n"
            "/analyze - AI Market Analysis\n"
            "/help - Command List\n\n"
            "*Emergency Controls:*\n"
            "/halt - Emergency Kill Switch\n"
            "/resume - Resume Trading\n"
            "/close\\_all - Close All Positions"
        )
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_auth(update, "/help"):
            return
        await self.cmd_start(update, context)

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status — comprehensive system status."""
        if not await self._check_auth(update, "/status"):
            return

        lines = ["*NEXUS System Status*\n"]
        lines.append(f"Time: `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`\n")

        # Ensemble status
        try:
            ensemble = get_ensemble()
            status = ensemble.get_status()
            lines.append(f"Decision Engine: {len(status.get('models', []))} models active")
        except Exception:
            lines.append("Decision Engine: unavailable")

        # Failsafe mode
        try:
            from security.failsafe import get_failsafe
            mode = get_failsafe().mode.value
            lines.append(f"System Mode: `{mode}`")
        except Exception:
            lines.append("System Mode: unknown")

        # Risk status
        try:
            from app.services.risk_governor import get_risk_status
            risk = get_risk_status()
            trading = risk.get("trading_enabled", False)
            drawdown = risk.get("drawdown", {}).get("current", 0)
            equity = risk.get("equity", {}).get("current", 0)
            lines.append(f"Trading: {'ENABLED' if trading else 'DISABLED'}")
            lines.append(f"Equity: `${equity:,.2f}`")
            lines.append(f"Drawdown: `{drawdown:.2f}%`")
        except Exception:
            lines.append("Risk: unavailable")

        # Capital lock
        try:
            from security.capital_lock import get_capital_lock
            locked = get_capital_lock().is_locked
            lines.append(f"Capital Lock: {'ACTIVE' if locked else 'inactive'}")
        except Exception:
            pass

        # MT5 connection
        try:
            from app.services.execution import get_engine
            engine = get_engine()
            mt5_ok = engine.mt5._initialized
            lines.append(f"MT5: {'connected' if mt5_ok else 'disconnected'}")
        except Exception:
            lines.append("MT5: unknown")

        # Config
        try:
            from config.config_loader import get_config
            cfg = get_config()
            lines.append(f"Environment: `{cfg.env_mode.value}`")
            lines.append(f"Risk Level: `{cfg.risk_level}`")
        except Exception:
            pass

        await update.message.reply_text("\n".join(lines), parse_mode='Markdown')

    async def cmd_signal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signal command."""
        if not await self._check_auth(update, "/signal"):
            return

        await update.message.reply_text("Analyzing current market state...")

        ensemble = get_ensemble()
        decision = ensemble.last_decision

        if not decision:
            await update.message.reply_text("No active signal generated yet. Waiting for market data.")
            return

        icon = ""
        if decision.final_prediction == Prediction.UP:
            icon = "UP"
        elif decision.final_prediction == Prediction.DOWN:
            icon = "DOWN"
        else:
            icon = "NEUTRAL"

        msg = (
            f"*SIGNAL: {icon}*\n"
            f"Confidence: `{decision.aggregated_confidence:.2f}`\n"
            f"Agreement: `{decision.agreement_score:.2f}`\n"
            f"Action: `{'HALT' if decision.should_halt else 'ACTIVE'}`\n\n"
            f"*Reasoning:*\n{decision.reasoning}"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def cmd_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command."""
        if not await self._check_auth(update, "/analyze"):
            return

        await update.message.reply_text("Requesting AI analysis...")

        try:
            from app.services.live_data import get_live_data
            manager = get_live_data()
            health = manager.check_data_integrity()

            if not health.get("has_data"):
                await update.message.reply_text(
                    "*Live Data Not Connected*\n"
                    "Cannot perform real-time analysis without active market feed.\n"
                    "Ensure live data is running.",
                    parse_mode='Markdown'
                )
                return

            msg = (
                "*Market Data Health*\n"
                f"Active Symbols: {health.get('active_symbols', 0)}\n"
                f"Last Update: {health.get('last_update', 'N/A')}"
            )
            await update.message.reply_text(msg, parse_mode='Markdown')

        except Exception as e:
            await update.message.reply_text(f"Analysis error: {e}")

    # =========================================================================
    # EMERGENCY COMMAND HANDLERS (Phase C)
    # =========================================================================

    async def cmd_halt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /halt — Emergency kill switch.

        HIGH-RISK: Requires confirmation via hardening layer.
        Triggers global halt + cancels all orders.
        """
        if not await self._check_auth(update, "/halt"):
            return

        logger.critical(f"TELEGRAM HALT COMMAND from user {update.effective_user.id}")

        try:
            # Global halt via circuit breaker
            from app.services.circuit_breaker import get_manager
            cb_manager = get_manager()
            cb_manager.global_halt("Telegram /halt command")

            # Kill switch via execution engine
            from app.services.execution import get_engine
            engine = get_engine()
            engine.kill_switch()

            # Emergency shutdown via risk governor
            from app.services.risk_governor import emergency_shutdown
            emergency_shutdown("Telegram /halt command")

            await update.message.reply_text(
                "*EMERGENCY HALT EXECUTED*\n\n"
                "All trading STOPPED.\n"
                "All pending orders CANCELLED.\n"
                "Circuit breaker TRIPPED.\n\n"
                "Use /resume to restart trading.",
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Telegram halt error: {e}")
            await update.message.reply_text(f"Halt execution error: {e}")

    async def cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /resume — Resume trading after halt.

        HIGH-RISK: Requires confirmation via hardening layer.
        """
        if not await self._check_auth(update, "/resume"):
            return

        logger.warning(f"TELEGRAM RESUME COMMAND from user {update.effective_user.id}")

        try:
            # Resume circuit breaker
            from app.services.circuit_breaker import get_manager
            cb_manager = get_manager()
            cb_manager.resume_trading()

            # Restore failsafe to SAFE_MODE (not directly NORMAL for safety)
            from security.failsafe import get_failsafe
            failsafe = get_failsafe()
            failsafe.enter_safe_mode("Telegram /resume — cautious restart", source="TELEGRAM")

            await update.message.reply_text(
                "*TRADING RESUMED*\n\n"
                "System Mode: SAFE\\_MODE\n"
                "Circuit breaker: RESET\n"
                "Risk governor: ACTIVE\n\n"
                "System operating in cautious mode.\n"
                "Use /status to check full state.",
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Telegram resume error: {e}")
            await update.message.reply_text(f"Resume error: {e}")

    async def cmd_close_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /close_all — Close all open positions.

        HIGH-RISK: Requires confirmation via hardening layer.
        """
        if not await self._check_auth(update, "/close_all"):
            return

        logger.critical(f"TELEGRAM CLOSE_ALL COMMAND from user {update.effective_user.id}")

        try:
            from app.services.execution import get_engine
            engine = get_engine()

            # Kill switch with no symbol = close all
            result = engine.kill_switch(None)

            await update.message.reply_text(
                "*ALL POSITIONS CLOSED*\n\n"
                f"Result: {result}\n\n"
                "Use /status to verify.",
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Telegram close_all error: {e}")
            await update.message.reply_text(f"Close all error: {e}")


# Global instance
_telegram_service: Optional[TelegramService] = None


def get_telegram_service() -> TelegramService:
    global _telegram_service
    if not _telegram_service:
        _telegram_service = TelegramService()
    return _telegram_service
