"""
NEXUS Telegram Reporter — Live Reporting System
=================================================

Phase 4, Part D: Telegram Notifications

1. Trade open notification — asset, lot, entry, SL/TP, risk %, confidence
2. Trade close notification — P&L, duration, exit reason
3. Daily summary at 23:59 — trades, win rate, net P&L, drawdown, equity
4. Emergency alerts — halt, daily loss cap, broker disconnect
"""

import asyncio
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("nexus.telegram")

# =============================================================================
# CONFIGURATION
# =============================================================================
TELEGRAM_BOT_TOKEN = os.environ.get("NEXUS_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("NEXUS_TELEGRAM_CHAT_ID", "")
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
DAILY_SUMMARY_HOUR = 23
DAILY_SUMMARY_MINUTE = 59
PERIODIC_SUMMARY_INTERVAL_HOURS = 4  # send summary every 4 hours


# =============================================================================
# TELEGRAM REPORTER
# =============================================================================

class TelegramReporter:
    """
    Sends structured messages to Telegram.

    If TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set,
    messages are logged but not sent (graceful degradation).
    """

    def __init__(self):
        self._token = TELEGRAM_BOT_TOKEN
        self._chat_id = TELEGRAM_CHAT_ID
        self._enabled = bool(self._token and self._chat_id)
        self._message_count = 0
        self._lock = threading.Lock()
        self._daily_summary_thread: Optional[threading.Thread] = None
        self._periodic_thread: Optional[threading.Thread] = None
        self._command_thread: Optional[threading.Thread] = None
        self._running = False

        if self._enabled:
            logger.info("Telegram reporter initialized (ACTIVE)")
        else:
            logger.info("Telegram reporter initialized (INACTIVE — no credentials)")

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    # ── Core Send ────────────────────────────────────────────────────────

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to the configured Telegram chat."""
        if not self._enabled:
            logger.info(f"TELEGRAM (disabled): {text[:100]}")
            return False

        try:
            import httpx
            url = TELEGRAM_API_URL.format(token=self._token)
            payload = {
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": parse_mode,
            }
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    with self._lock:
                        self._message_count += 1
                    return True
                else:
                    logger.error(f"Telegram send failed: {resp.status_code} {resp.text[:200]}")
                    return False
        except ImportError:
            logger.warning("httpx not available — Telegram send skipped")
            return False
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False

    def send_emergency_sync(self, text: str) -> bool:
        """Synchronous send for crash/emergency contexts."""
        if not self._enabled:
            logger.info(f"TELEGRAM EMERGENCY (disabled): {text[:100]}")
            return False

        try:
            import urllib.request
            import json
            url = TELEGRAM_API_URL.format(token=self._token)
            payload = json.dumps({
                "chat_id": self._chat_id,
                "text": f"🚨 NEXUS EMERGENCY 🚨\n\n{text}",
                "parse_mode": "HTML",
            }).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=10)
            return resp.status == 200
        except Exception as e:
            logger.error(f"Telegram emergency send error: {e}")
            return False

    # ── Trade Open ───────────────────────────────────────────────────────

    async def notify_trade_open(
        self,
        symbol: str,
        side: str,
        lot_size: float,
        entry_price: float,
        stop_loss: Optional[float],
        take_profit: Optional[float],
        risk_pct: float,
        confidence: float,
    ) -> bool:
        """Send trade open notification."""
        sl_str = f"${stop_loss:,.5f}" if stop_loss else "None"
        tp_str = f"${take_profit:,.5f}" if take_profit else "None"
        direction = "🟢 BUY" if side.upper() == "BUY" else "🔴 SELL"

        text = (
            f"<b>📊 TRADE OPENED</b>\n\n"
            f"<b>{direction} {symbol}</b>\n"
            f"Lot Size: <code>{lot_size}</code>\n"
            f"Entry: <code>${entry_price:,.5f}</code>\n"
            f"SL: <code>{sl_str}</code>\n"
            f"TP: <code>{tp_str}</code>\n"
            f"Risk: <code>{risk_pct:.2f}%</code>\n"
            f"Confidence: <code>{confidence:.0%}</code>\n"
            f"Time: <code>{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}</code>"
        )
        return await self.send_message(text)

    # ── Trade Close ──────────────────────────────────────────────────────

    async def notify_trade_close(
        self,
        symbol: str,
        side: str,
        pnl_dollars: float,
        pnl_pct: float,
        duration_mins: float,
        exit_reason: str,
    ) -> bool:
        """Send trade close notification."""
        emoji = "✅" if pnl_dollars >= 0 else "❌"
        pnl_sign = "+" if pnl_dollars >= 0 else ""

        text = (
            f"<b>{emoji} TRADE CLOSED</b>\n\n"
            f"<b>{symbol} ({side})</b>\n"
            f"P/L: <code>{pnl_sign}${pnl_dollars:,.2f} ({pnl_sign}{pnl_pct:.2f}%)</code>\n"
            f"Duration: <code>{duration_mins:.0f} min</code>\n"
            f"Exit: <code>{exit_reason}</code>\n"
            f"Time: <code>{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}</code>"
        )
        return await self.send_message(text)

    # ── Daily Summary ────────────────────────────────────────────────────

    async def send_daily_summary(self, summary: Dict[str, Any]) -> bool:
        """Send end-of-day performance summary."""
        pnl = summary.get("daily_pnl", 0)
        pnl_pct = summary.get("daily_pnl_pct", 0)
        pnl_sign = "+" if pnl >= 0 else ""
        emoji = "📈" if pnl >= 0 else "📉"

        text = (
            f"<b>{emoji} DAILY SUMMARY — {summary.get('date', 'N/A')}</b>\n\n"
            f"Total Trades: <code>{summary.get('trades_today', 0)}</code>\n"
            f"Win Rate: <code>{summary.get('win_rate', 0):.1f}%</code>\n"
            f"Net P/L: <code>{pnl_sign}${pnl:,.2f} ({pnl_sign}{pnl_pct:.2f}%)</code>\n"
            f"Max Drawdown: <code>{summary.get('max_drawdown', 0):.2f}%</code>\n"
            f"Equity: <code>${summary.get('current_equity', 0):,.2f}</code>\n"
            f"Wins: {summary.get('wins', 0)} | Losses: {summary.get('losses', 0)}"
        )
        return await self.send_message(text)

    # ── Emergency Alerts ─────────────────────────────────────────────────

    async def send_emergency_alert(self, reason: str, details: str = "") -> bool:
        """Send emergency alert."""
        text = (
            f"<b>🚨 EMERGENCY ALERT 🚨</b>\n\n"
            f"<b>Reason:</b> <code>{reason}</code>\n"
        )
        if details:
            text += f"<b>Details:</b> <code>{details}</code>\n"
        text += f"<b>Time:</b> <code>{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}</code>"
        return await self.send_message(text)

    # ── Periodic Summary (every 4 hours) ────────────────────────────────

    async def send_periodic_summary(self) -> bool:
        """Send 4-hour periodic summary with key metrics."""
        try:
            # Gather data
            equity = 0.0
            daily_pnl = 0.0
            open_positions = 0
            risk_exposure = 0.0
            system_mode = "UNKNOWN"
            health_status = "UNKNOWN"

            try:
                from app.services import risk_governor
                risk = risk_governor.get_risk_status()
                equity = risk.get("equity", {}).get("current", 0)
                daily_pnl = risk.get("total_pnl_pct", 0)
                open_positions = risk.get("open_positions_count", 0)
                risk_exposure = risk.get("drawdown", {}).get("current", 0)
            except Exception:
                pass

            try:
                from app.services.watchdog import get_watchdog
                system_mode = get_watchdog().get_mode().value
            except Exception:
                pass

            try:
                from app.services.health_monitor import get_health_monitor
                result = get_health_monitor().get_latest_result()
                health_status = result.get("overall_status", "UNKNOWN") if result else "NO_DATA"
            except Exception:
                pass

            pnl_sign = "+" if daily_pnl >= 0 else ""
            pnl_emoji = "📈" if daily_pnl >= 0 else "📉"

            text = (
                f"<b>📊 PERIODIC REPORT</b>\n\n"
                f"Equity: <code>${equity:,.2f}</code>\n"
                f"Daily P/L: <code>{pnl_sign}{daily_pnl:.2f}%</code> {pnl_emoji}\n"
                f"Open Positions: <code>{open_positions}</code>\n"
                f"Risk Exposure: <code>{risk_exposure:.2f}%</code>\n"
                f"System Mode: <code>{system_mode}</code>\n"
                f"Health: <code>{health_status}</code>\n"
                f"Time: <code>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</code>"
            )
            return await self.send_message(text)
        except Exception as e:
            logger.error(f"Periodic summary error: {e}")
            return False

    # ── Command Handlers (/status, /health) ───────────────────────────

    def generate_status_report(self) -> str:
        """Generate full diagnostic report for /status command."""
        lines = ["<b>📋 NEXUS STATUS REPORT</b>\n"]

        # System mode
        try:
            from app.services.watchdog import get_watchdog
            mode = get_watchdog().get_mode().value
            lines.append(f"Mode: <code>{mode}</code>")
        except Exception:
            lines.append("Mode: <code>UNKNOWN</code>")

        # Equity and P&L
        try:
            from app.services import risk_governor
            risk = risk_governor.get_risk_status()
            eq = risk.get("equity", {})
            lines.append(f"\n<b>Capital:</b>")
            lines.append(f"  Equity: <code>${eq.get('current', 0):,.2f}</code>")
            lines.append(f"  Peak: <code>${eq.get('peak', 0):,.2f}</code>")
            lines.append(f"  Drawdown: <code>{risk.get('drawdown', {}).get('current', 0):.2f}%</code>")
            lines.append(f"  P&L: <code>{risk.get('total_pnl_pct', 0):+.2f}%</code>")
        except Exception:
            pass

        # Daily stats
        try:
            from app.services.capital_protection import get_daily_tracker
            daily = get_daily_tracker().get_daily_summary()
            lines.append(f"\n<b>Today:</b>")
            lines.append(f"  Trades: <code>{daily.get('trades_today', 0)}</code>")
            lines.append(f"  Win Rate: <code>{daily.get('win_rate', 0):.0f}%</code>")
            lines.append(f"  P&L: <code>{daily.get('daily_pnl_pct', 0):+.2f}%</code>")
            lines.append(f"  Cap Hit: <code>{daily.get('cap_hit', False)}</code>")
        except Exception:
            pass

        # Open positions
        try:
            from app.services import risk_governor
            state = risk_governor._get_state()
            pos_count = len(state.open_positions)
            lines.append(f"\n<b>Positions:</b> <code>{pos_count}</code>")
            for sym, pos in list(state.open_positions.items())[:5]:
                lines.append(f"  {sym}: <code>{pos.get('side', '?')} {pos.get('quantity', '?')}</code>")
        except Exception:
            pass

        # Performance metrics
        try:
            from app.services.performance_metrics import get_performance_metrics_engine
            metrics = get_performance_metrics_engine().get_metrics()
            if metrics.get("total_trades", 0) > 0:
                lines.append(f"\n<b>Performance:</b>")
                lines.append(f"  Win Rate: <code>{metrics.get('win_rate_pct', 0):.1f}%</code>")
                lines.append(f"  Profit Factor: <code>{metrics.get('profit_factor', 0):.2f}</code>")
                lines.append(f"  R:R Ratio: <code>{metrics.get('risk_reward_ratio', 0):.2f}</code>")
        except Exception:
            pass

        lines.append(f"\n<code>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</code>")
        return "\n".join(lines)

    def generate_health_report(self) -> str:
        """Generate infrastructure health report for /health command."""
        lines = ["<b>🏥 NEXUS HEALTH REPORT</b>\n"]

        try:
            from app.services.health_monitor import get_health_monitor
            result = get_health_monitor().get_latest_result()
            if result:
                status = result.get("overall_status", "UNKNOWN")
                status_emoji = {"HEALTHY": "✅", "DEGRADED": "⚠️", "CRITICAL": "🚨"}.get(status, "❓")
                lines.append(f"Status: {status_emoji} <code>{status}</code>")
                lines.append(f"MT5: <code>{'Connected' if result.get('mt5_connected') else 'DISCONNECTED'}</code>")
                lines.append(f"Memory: <code>{result.get('memory_mb', 0):.0f}MB</code>")
                lines.append(f"Disk: <code>{result.get('disk_free_mb', 0):.0f}MB free</code>")
                lines.append(f"Exec Latency: <code>{result.get('execution_latency_avg_ms', 0):.0f}ms</code>")
                lines.append(f"API Latency: <code>{result.get('api_latency_avg_ms', 0):.0f}ms</code>")
                lines.append(f"Position Sync: <code>{'OK' if result.get('position_sync_ok') else 'DESYNC'}</code>")
                lines.append(f"Registry: <code>{'OK' if result.get('state_registry_ok') else 'ERROR'}</code>")

                issues = result.get("issues", [])
                if issues:
                    lines.append(f"\n<b>Issues ({len(issues)}):</b>")
                    for issue in issues[:5]:
                        lines.append(f"  ⚠️ <code>{issue}</code>")
            else:
                lines.append("No health data available yet.")
        except Exception as e:
            lines.append(f"Error fetching health: <code>{e}</code>")

        # Fail-safe status
        try:
            from app.services.fail_safe import get_fail_safe
            fs = get_fail_safe().get_status()
            lines.append(f"\n<b>Fail-Safe:</b>")
            lines.append(f"  Frozen: <code>{fs.get('frozen', False)}</code>")
            if fs.get("frozen"):
                lines.append(f"  Reason: <code>{fs.get('freeze_reason', '')}</code>")
        except Exception:
            pass

        lines.append(f"\n<code>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</code>")
        return "\n".join(lines)

    async def handle_command(self, command: str) -> bool:
        """Handle incoming Telegram commands."""
        cmd = command.strip().lower()
        if cmd == "/status":
            report = self.generate_status_report()
            return await self.send_message(report)
        elif cmd == "/health":
            report = self.generate_health_report()
            return await self.send_message(report)
        return False

    # ── Daily Summary Scheduler ──────────────────────────────────────────

    def start_daily_summary_scheduler(self) -> None:
        """Start background threads for daily summary and periodic reports."""
        if self._running:
            return
        self._running = True
        self._daily_summary_thread = threading.Thread(
            target=self._daily_summary_loop, daemon=True, name="nexus-telegram-daily"
        )
        self._daily_summary_thread.start()

        # Start periodic summary thread
        self._periodic_thread = threading.Thread(
            target=self._periodic_summary_loop, daemon=True, name="nexus-telegram-periodic"
        )
        self._periodic_thread.start()

        # Start command listener thread
        self._command_thread = threading.Thread(
            target=self._command_listener_loop, daemon=True, name="nexus-telegram-commands"
        )
        self._command_thread.start()

    def stop(self) -> None:
        self._running = False
        if self._daily_summary_thread:
            self._daily_summary_thread.join(timeout=5)
        if self._periodic_thread:
            self._periodic_thread.join(timeout=5)
        if self._command_thread:
            self._command_thread.join(timeout=5)

    def _daily_summary_loop(self) -> None:
        """Wait until 23:59 UTC each day and send summary."""
        last_sent_date = ""
        while self._running:
            now = datetime.now(timezone.utc)
            today = now.strftime("%Y-%m-%d")

            if (
                now.hour == DAILY_SUMMARY_HOUR
                and now.minute >= DAILY_SUMMARY_MINUTE
                and today != last_sent_date
            ):
                try:
                    from app.services.capital_protection import get_daily_tracker
                    summary = get_daily_tracker().get_daily_summary()

                    # Add max drawdown from risk governor
                    try:
                        from app.services import risk_governor
                        risk = risk_governor.get_risk_status()
                        summary["max_drawdown"] = risk.get("drawdown", {}).get("current", 0)
                    except Exception:
                        summary["max_drawdown"] = 0

                    # Run async send in a new event loop for this thread
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(self.send_daily_summary(summary))
                    loop.close()

                    last_sent_date = today
                    logger.info(f"Daily summary sent for {today}")
                except Exception as e:
                    logger.error(f"Daily summary send error: {e}")

            time.sleep(30)  # check every 30 seconds

    def _periodic_summary_loop(self) -> None:
        """Send periodic summary every 4 hours."""
        while self._running:
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.send_periodic_summary())
                loop.close()
                logger.info("Periodic summary sent")
            except Exception as e:
                logger.error(f"Periodic summary error: {e}")
            # Sleep for 4 hours
            for _ in range(PERIODIC_SUMMARY_INTERVAL_HOURS * 3600):
                if not self._running:
                    return
                time.sleep(1)

    def _command_listener_loop(self) -> None:
        """Poll Telegram for /status and /health commands."""
        if not self._enabled:
            return

        last_update_id = 0
        while self._running:
            try:
                import urllib.request
                import json as json_mod
                url = f"https://api.telegram.org/bot{self._token}/getUpdates?offset={last_update_id + 1}&timeout=10"
                req = urllib.request.Request(url)
                resp = urllib.request.urlopen(req, timeout=15)
                data = json_mod.loads(resp.read())

                if data.get("ok"):
                    for update in data.get("result", []):
                        update_id = update.get("update_id", 0)
                        if update_id > last_update_id:
                            last_update_id = update_id
                        msg = update.get("message", {})
                        text = msg.get("text", "")
                        chat_id = str(msg.get("chat", {}).get("id", ""))
                        # Only respond to our configured chat
                        if chat_id == self._chat_id and text.startswith("/"):
                            loop = asyncio.new_event_loop()
                            loop.run_until_complete(self.handle_command(text))
                            loop.close()
            except Exception:
                pass  # Silent — don't spam logs for polling failures
            time.sleep(5)

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "enabled": self._enabled,
                "message_count": self._message_count,
                "daily_scheduler_running": self._running,
            }


# =============================================================================
# SINGLETON
# =============================================================================

_reporter: Optional[TelegramReporter] = None


def get_telegram_reporter() -> TelegramReporter:
    global _reporter
    if _reporter is None:
        _reporter = TelegramReporter()
    return _reporter
