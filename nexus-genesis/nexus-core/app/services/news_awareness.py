"""
NEXUS News Awareness Layer — Phase 5, Part C
==============================================

Read-only economic calendar awareness. No prediction of outcomes.
Risk awareness only.

Rules:
  - No new trades X minutes before/after high-impact events
  - Existing trades may tighten stops
  - AI explanations reference news state

Supports manual calendar updates and optional API integration.
"""

import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.news_awareness")


# =============================================================================
# CONFIGURATION
# =============================================================================
NEWS_BLACKOUT_BEFORE_MINS = int(os.environ.get("NEXUS_NEWS_BLACKOUT_BEFORE", "30"))
NEWS_BLACKOUT_AFTER_MINS = int(os.environ.get("NEXUS_NEWS_BLACKOUT_AFTER", "15"))


# =============================================================================
# EVENT DEFINITIONS
# =============================================================================

class EventImpact(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EventCategory(Enum):
    CPI = "CPI"
    NFP = "NFP"
    FOMC = "FOMC"
    INTEREST_RATE = "INTEREST_RATE"
    GDP = "GDP"
    EARNINGS = "EARNINGS"
    PMI = "PMI"
    EMPLOYMENT = "EMPLOYMENT"
    RETAIL_SALES = "RETAIL_SALES"
    OTHER = "OTHER"


@dataclass
class EconomicEvent:
    """A single economic calendar event."""
    event_id: str
    name: str
    category: EventCategory
    impact: EventImpact
    currency: str            # affected currency (e.g. "USD", "EUR")
    scheduled_time: datetime
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "name": self.name,
            "category": self.category.value,
            "impact": self.impact.value,
            "currency": self.currency,
            "scheduled_time": self.scheduled_time.isoformat(),
            "description": self.description,
        }


# =============================================================================
# CURRENCY-TO-SYMBOL MAPPING
# =============================================================================

# Maps currency codes to symbols they affect
CURRENCY_SYMBOL_MAP: Dict[str, List[str]] = {
    "USD": ["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD", "ETHUSD", "BTC/USDT", "ETH/USDT"],
    "EUR": ["EURUSD"],
    "GBP": ["GBPUSD"],
    "JPY": [],
    "CHF": [],
    "AUD": [],
    "CAD": [],
    "NZD": [],
}


def _get_affected_symbols(currency: str) -> List[str]:
    """Get symbols affected by a currency's events."""
    return CURRENCY_SYMBOL_MAP.get(currency.upper(), [])


# =============================================================================
# NEWS CALENDAR
# =============================================================================

class NewsCalendar:
    """
    In-memory economic calendar for high-impact events.

    Events can be loaded manually or from an external source.
    Thread-safe for concurrent read/write.
    """

    def __init__(self):
        self._events: List[EconomicEvent] = []
        self._lock = threading.Lock()

    def add_event(self, event: EconomicEvent) -> None:
        """Add a single event to the calendar."""
        with self._lock:
            self._events.append(event)
            self._events.sort(key=lambda e: e.scheduled_time)
        logger.info(f"NEWS_EVENT_ADDED: {event.name} at {event.scheduled_time.isoformat()}")

    def add_events(self, events: List[EconomicEvent]) -> None:
        """Bulk add events."""
        with self._lock:
            self._events.extend(events)
            self._events.sort(key=lambda e: e.scheduled_time)
        logger.info(f"NEWS_EVENTS_LOADED: {len(events)} events added")

    def clear_past_events(self) -> int:
        """Remove events older than 24 hours. Returns count removed."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        with self._lock:
            before = len(self._events)
            self._events = [e for e in self._events if e.scheduled_time > cutoff]
            removed = before - len(self._events)
        return removed

    def get_upcoming_events(
        self,
        hours_ahead: int = 24,
        impact_filter: Optional[EventImpact] = None,
    ) -> List[EconomicEvent]:
        """Get events within the next N hours."""
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours_ahead)
        with self._lock:
            events = [
                e for e in self._events
                if now <= e.scheduled_time <= cutoff
            ]
            if impact_filter:
                events = [e for e in events if e.impact == impact_filter]
        return events

    def is_in_blackout_window(self, symbol: str) -> Tuple[bool, Optional[EconomicEvent]]:
        """
        Check if a symbol is within the news blackout window.

        Returns:
            (in_blackout, nearest_event_or_None)
        """
        now = datetime.now(timezone.utc)
        before_delta = timedelta(minutes=NEWS_BLACKOUT_BEFORE_MINS)
        after_delta = timedelta(minutes=NEWS_BLACKOUT_AFTER_MINS)

        with self._lock:
            for event in self._events:
                if event.impact != EventImpact.HIGH:
                    continue

                # Check if symbol is affected by this event's currency
                affected_symbols = _get_affected_symbols(event.currency)
                if symbol not in affected_symbols:
                    continue

                window_start = event.scheduled_time - before_delta
                window_end = event.scheduled_time + after_delta

                if window_start <= now <= window_end:
                    return True, event

        return False, None

    def get_news_context_for_ai(self, symbol: str) -> str:
        """
        Get formatted news context for AI prompt injection.
        """
        in_blackout, event = self.is_in_blackout_window(symbol)

        if in_blackout and event:
            return (
                f"NEWS RISK ACTIVE FOR {symbol}:\n"
                f"  Event: {event.name} ({event.category.value})\n"
                f"  Impact: {event.impact.value}\n"
                f"  Scheduled: {event.scheduled_time.strftime('%H:%M UTC')}\n"
                f"  Status: BLACKOUT WINDOW — no new trades permitted.\n"
                f"  Guidance: News-risk filtered. Avoid new entries."
            )

        # Check upcoming events
        upcoming = self.get_upcoming_events(hours_ahead=4, impact_filter=EventImpact.HIGH)
        relevant = []
        for e in upcoming:
            affected = _get_affected_symbols(e.currency)
            if symbol in affected:
                relevant.append(e)

        if relevant:
            lines = [f"NEWS AWARENESS FOR {symbol}:"]
            for e in relevant[:3]:  # max 3 events
                time_str = e.scheduled_time.strftime("%H:%M UTC")
                mins_until = int((e.scheduled_time - datetime.now(timezone.utc)).total_seconds() / 60)
                lines.append(
                    f"  [{e.impact.value}] {e.name} at {time_str} "
                    f"(in {mins_until} min) — {e.currency}"
                )
            lines.append("  Status: News-aware. Monitor closely.")
            return "\n".join(lines)

        return f"NEWS STATUS FOR {symbol}: News-neutral. No high-impact events nearby."

    def get_all_events_dict(self) -> List[Dict[str, Any]]:
        """Get all events as dicts (for API)."""
        with self._lock:
            return [e.to_dict() for e in self._events]


# =============================================================================
# SINGLETON
# =============================================================================

_calendar: Optional[NewsCalendar] = None


def get_news_calendar() -> NewsCalendar:
    global _calendar
    if _calendar is None:
        _calendar = NewsCalendar()
    return _calendar
