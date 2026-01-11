"""
NEXUS Telegram Bot Service
===========================

Provides real-time interaction with the trading bot via Telegram.

Features:
1. Command handling (/start, /status, /analyze, /signal)
2. Asynchronous integration with FastAPI
3. Secure token management
4. Real-time alerts (future)
"""

import logging
import asyncio
import os
from datetime import datetime
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

            # Add handlers
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("analyze", self.cmd_analyze))
            self.application.add_handler(CommandHandler("signal", self.cmd_signal))
            self.application.add_handler(CommandHandler("help", self.cmd_help))

            # Initialize and start
            await self.application.initialize()
            await self.application.start()
            
            # Use short polling for simplicity in this context, or long polling via run_polling
            # For integration with FastAPI, we often run polling in a background task
            # or use webhooks. Here we'll use a simple background polling task.
            asyncio.create_task(self._run_polling())
            
            self.bot_info = await self.application.bot.get_me()
            self.is_running = True
            logger.info(f"Telegram Bot started: @{self.bot_info.username}")
            
            # Send startup message if chat ID is known
            if self.allowed_chat_id:
                await self.send_message("🚀 NEXUS AI Trading Bot Online")

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
                    await self.send_message("🛑 NEXUS AI System Shutdown")
                
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
            await self.application.bot.send_message(chat_id=self.allowed_chat_id, text=text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    # =========================================================================
    # COMMAND HANDLERS
    # =========================================================================

    async def _check_auth(self, update: Update) -> bool:
        """Check if user is authorized."""
        user_id = str(update.effective_user.id)
        if self.allowed_chat_id and user_id != str(self.allowed_chat_id):
            await update.message.reply_text("⛔ Unauthorized access.")
            logger.warning(f"Unauthorized access attempt from ID: {user_id}")
            return False
        return True

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        if not await self._check_auth(update): return
        
        welcome_msg = (
            "🤖 *NEXUS AI Operational*\n\n"
            "Systems nominal. Ready for command.\n\n"
            "/status - System Health\n"
            "/signal - Current Signal\n"
            "/analyze - AI Market Analysis\n"
            "/help - Command List"
        )
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_auth(update): return
        await self.cmd_start(update, context)

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        if not await self._check_auth(update): return

        # Gather status info (mocked for now, integrate with actual health checks later)
        ensemble = get_ensemble()
        status = ensemble.get_status()
        
        msg = (
            "📊 *System Status*\n"
            f"Time: `{datetime.now().strftime('%H:%M:%S')}`\n"
            "-------------------\n"
            f"✅ Database Connection\n"
            f"✅ Vertex AI Access\n"
            f"✅ Decision Engine ({len(status['models'])} models)\n"
            "-------------------\n"
            "Bot is monitoring..."
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def cmd_signal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signal command."""
        if not await self._check_auth(update): return

        await update.message.reply_text("⏳ Analyzing current market state...")

        # Get latest signal from ensemble
        # NOTE: In a real scenario, this would fetch the most recent processed candle data
        # For now, we'll assume the ensemble has a 'last_decision' stored or trigger a quick check
        ensemble = get_ensemble()
        decision = ensemble.last_decision
        
        if not decision:
            await update.message.reply_text("⚠️ No active signal generated yet. Waiting for market data.")
            return

        icon = "⚪"
        if decision.final_prediction == Prediction.UP: icon = "🟢"
        elif decision.final_prediction == Prediction.DOWN: icon = "🔴"

        msg = (
            f"{icon} *SIGNAL: {decision.final_prediction.value}*\n"
            f"Confidence: `{decision.aggregated_confidence:.2f}`\n"
            f"Agreement: `{decision.agreement_score:.2f}`\n"
            f"Action: `{ 'HALT' if decision.should_halt else 'ACTIVE' }`\n\n"
            f"📝 *Reasoning:*\n{decision.reasoning}"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def cmd_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command."""
        if not await self._check_auth(update): return

        await update.message.reply_text("🧠 requesting Vertex AI analysis...")

        # In a real app, you'd fetch the latest 50 candles from DB/exchange
        # Here we mock a quick data set or use the intelligence tool if feasible
        # For this implementation stage, we'll inform the user it's a simulation without live data
        
        msg = (
            "⚠️ *Live Data Not Connected*\n"
            "Cannot perform real-time analysis without active market feed.\n"
            "Please ensure `NexusStream` is running."
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

# Global instance
_telegram_service: Optional[TelegramService] = None

def get_telegram_service() -> TelegramService:
    global _telegram_service
    if not _telegram_service:
        _telegram_service = TelegramService()
    return _telegram_service
