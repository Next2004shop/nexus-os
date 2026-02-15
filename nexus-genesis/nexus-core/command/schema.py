"""
NEXUS Command Layer — Schema
==============================

Pydantic model defining the strict structure of every trade command.
All trades must be expressed as a TradeCommand before processing.
"""

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class TradeCommand(BaseModel):
    """
    Strict trade command schema.
    
    Every trade — AI, manual, or system — must be encoded as this model
    before it can be validated, routed, or executed.
    """
    asset: str = Field(..., description="Trading symbol, e.g. XAUUSD")
    direction: Literal["buy", "sell"] = Field(..., description="Trade direction")
    lot_size: float = Field(..., gt=0, description="Position size in lots")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    source: Literal["ai", "manual", "system"] = Field(..., description="Command origin")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Command creation time (UTC)"
    )

    @field_validator("asset")
    @classmethod
    def asset_uppercase(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("stop_loss", "take_profit")
    @classmethod
    def price_must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Price must be positive")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "asset": "XAUUSD",
                "direction": "buy",
                "lot_size": 0.1,
                "stop_loss": 2300.0,
                "take_profit": 2400.0,
                "source": "manual",
                "timestamp": "2026-02-15T12:00:00Z"
            }
        }
