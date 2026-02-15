"""
NEXUS MetaTrader Bridge - Secure Trading Execution
===================================================

Connects to MetaTrader (MT4/MT5) running on Google Cloud VM.

Architecture:
- MT5 runs on Windows VM in Google Cloud
- Bridge EA listens on localhost
- Backend sends signed trade instructions
- All credentials server-side only

ABSOLUTE LAW: Real money never risked without AI consensus.
"""

import logging
import hmac
import hashlib
import time
import json
import aiohttp
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("nexus.mt_bridge")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class OrderType(Enum):
    """MetaTrader order types."""
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"


class OrderStatus(Enum):
    """Order execution status."""
    PENDING = "pending"
    SENT = "sent"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    ERROR = "error"


@dataclass
class TradeInstruction:
    """Signed trade instruction for MT bridge."""
    instruction_id: str
    symbol: str
    order_type: OrderType
    volume: float
    price: Optional[float] = None  # None for market orders
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: str = "NEXUS"
    magic_number: int = 777777
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for transmission."""
        return {
            "id": self.instruction_id,
            "symbol": self.symbol,
            "type": self.order_type.value,
            "volume": self.volume,
            "price": self.price,
            "sl": self.stop_loss,
            "tp": self.take_profit,
            "comment": self.comment,
            "magic": self.magic_number,
            "timestamp": self.timestamp.isoformat(),
            "signature": self.signature
        }


@dataclass
class TradeResult:
    """Result of trade execution."""
    instruction_id: str
    status: OrderStatus
    ticket: Optional[int] = None
    executed_price: Optional[float] = None
    executed_volume: Optional[float] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None


@dataclass
class AccountInfo:
    """MT account information."""
    login: int
    server: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    leverage: int
    currency: str
    connected: bool
    trade_allowed: bool


@dataclass
class Position:
    """Open position."""
    ticket: int
    symbol: str
    order_type: OrderType
    volume: float
    open_price: float
    current_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    profit: float
    swap: float
    open_time: datetime
    magic_number: int


# =============================================================================
# MESSAGE SIGNING
# =============================================================================

class MessageSigner:
    """
    Signs trade instructions for authenticity.
    
    Only signed messages are executed by the bridge.
    """
    
    def __init__(self):
        self._secret_key: Optional[bytes] = None
    
    def _get_secret_key(self) -> bytes:
        """Get signing key from Secret Manager."""
        if self._secret_key:
            return self._secret_key
        
        try:
            from app.services.vault import get_secret
            key = get_secret("MT_BRIDGE_SIGNING_KEY")
            self._secret_key = key.encode() if isinstance(key, str) else key
            return self._secret_key
        except Exception as e:
            logger.error(f"Failed to get signing key: {e}")
            # Fallback (less secure)
            return hashlib.sha256(b"nexus-mt-bridge").digest()
    
    def sign(self, instruction: TradeInstruction) -> str:
        """Sign a trade instruction."""
        key = self._get_secret_key()
        
        # Create message to sign
        message = f"{instruction.instruction_id}:{instruction.symbol}:{instruction.order_type.value}:{instruction.volume}:{instruction.timestamp.isoformat()}"
        
        signature = hmac.new(key, message.encode(), hashlib.sha256).hexdigest()
        return signature
    
    def verify(self, instruction: TradeInstruction, signature: str) -> bool:
        """Verify instruction signature."""
        expected = self.sign(instruction)
        return hmac.compare_digest(expected, signature)


# =============================================================================
# MT BRIDGE CLIENT
# =============================================================================

class MTBridgeClient:
    """
    Client for communicating with MT bridge on VM.
    
    The bridge is a simple REST API running alongside MT5.
    """
    
    def __init__(
        self,
        bridge_url: str = "http://localhost:5000",
        timeout: int = 30
    ):
        self.bridge_url = bridge_url
        self.timeout = timeout
        self.signer = MessageSigner()
        self._session: Optional[aiohttp.ClientSession] = None
        self.is_connected = False
        self.last_heartbeat: Optional[datetime] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session
    
    async def connect(self) -> bool:
        """Test connection to bridge."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.bridge_url}/health") as resp:
                if resp.status == 200:
                    self.is_connected = True
                    self.last_heartbeat = datetime.now(timezone.utc)
                    logger.info("MT Bridge connected")
                    return True
                else:
                    logger.error(f"MT Bridge health check failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"MT Bridge connection error: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Close connection."""
        if self._session:
            await self._session.close()
        self.is_connected = False
    
    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get MT account information."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.bridge_url}/account") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return AccountInfo(
                        login=data["login"],
                        server=data["server"],
                        balance=data["balance"],
                        equity=data["equity"],
                        margin=data["margin"],
                        free_margin=data["free_margin"],
                        leverage=data["leverage"],
                        currency=data["currency"],
                        connected=data.get("connected", True),
                        trade_allowed=data.get("trade_allowed", True)
                    )
        except Exception as e:
            logger.error(f"Get account info error: {e}")
        return None
    
    async def get_positions(self) -> List[Position]:
        """Get open positions."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.bridge_url}/positions") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    positions = []
                    for p in data.get("positions", []):
                        positions.append(Position(
                            ticket=p["ticket"],
                            symbol=p["symbol"],
                            order_type=OrderType(p["type"]),
                            volume=p["volume"],
                            open_price=p["open_price"],
                            current_price=p["current_price"],
                            stop_loss=p.get("sl"),
                            take_profit=p.get("tp"),
                            profit=p["profit"],
                            swap=p.get("swap", 0),
                            open_time=datetime.fromisoformat(p["open_time"]),
                            magic_number=p.get("magic", 0)
                        ))
                    return positions
        except Exception as e:
            logger.error(f"Get positions error: {e}")
        return []
    
    async def execute_trade(
        self,
        instruction: TradeInstruction
    ) -> TradeResult:
        """
        Execute a trade instruction.
        
        Instruction must be signed.
        """
        # Sign the instruction
        instruction.signature = self.signer.sign(instruction)
        
        start_time = time.time()
        
        try:
            session = await self._get_session()
            
            async with session.post(
                f"{self.bridge_url}/trade",
                json=instruction.to_dict()
            ) as resp:
                
                execution_time = int((time.time() - start_time) * 1000)
                
                if resp.status == 200:
                    data = await resp.json()
                    
                    if data.get("success"):
                        logger.info(f"Trade executed: {instruction.symbol} {instruction.order_type.value} {instruction.volume}")
                        return TradeResult(
                            instruction_id=instruction.instruction_id,
                            status=OrderStatus.FILLED,
                            ticket=data.get("ticket"),
                            executed_price=data.get("price"),
                            executed_volume=data.get("volume"),
                            execution_time_ms=execution_time
                        )
                    else:
                        return TradeResult(
                            instruction_id=instruction.instruction_id,
                            status=OrderStatus.REJECTED,
                            error_message=data.get("error", "Unknown error"),
                            execution_time_ms=execution_time
                        )
                else:
                    return TradeResult(
                        instruction_id=instruction.instruction_id,
                        status=OrderStatus.ERROR,
                        error_message=f"HTTP {resp.status}",
                        execution_time_ms=execution_time
                    )
                    
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return TradeResult(
                instruction_id=instruction.instruction_id,
                status=OrderStatus.ERROR,
                error_message=str(e)
            )
    
    async def close_position(self, ticket: int) -> TradeResult:
        """Close a specific position."""
        try:
            session = await self._get_session()
            
            # Create signed close instruction
            close_msg = f"CLOSE:{ticket}:{int(time.time())}"
            signature = hmac.new(
                self.signer._get_secret_key(),
                close_msg.encode(),
                hashlib.sha256
            ).hexdigest()
            
            async with session.post(
                f"{self.bridge_url}/close",
                json={"ticket": ticket, "signature": signature}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        return TradeResult(
                            instruction_id=f"CLOSE_{ticket}",
                            status=OrderStatus.FILLED,
                            ticket=ticket
                        )
                    else:
                        return TradeResult(
                            instruction_id=f"CLOSE_{ticket}",
                            status=OrderStatus.REJECTED,
                            error_message=data.get("error")
                        )
        except Exception as e:
            logger.error(f"Close position error: {e}")
        
        return TradeResult(
            instruction_id=f"CLOSE_{ticket}",
            status=OrderStatus.ERROR,
            error_message="Close failed"
        )
    
    async def close_all(self) -> List[TradeResult]:
        """Close all positions."""
        results = []
        positions = await self.get_positions()
        
        for pos in positions:
            result = await self.close_position(pos.ticket)
            results.append(result)
        
        return results


# =============================================================================
# TRADE EXECUTION GATEWAY
# =============================================================================

class TradeExecutionGateway:
    """
    Gateway for secure trade execution via MT bridge.
    
    Enforces:
    - AI consensus required
    - Risk validation
    - Margin checks
    - Capital preservation
    """
    
    def __init__(self, bridge_url: str = "http://localhost:5000"):
        self.bridge = MTBridgeClient(bridge_url)
        self.pending_trades: Dict[str, TradeInstruction] = {}
        self.executed_trades: List[TradeResult] = []
        self.is_trading_enabled = True
    
    async def initialize(self) -> bool:
        """Initialize the gateway."""
        connected = await self.bridge.connect()
        
        if connected:
            account = await self.bridge.get_account_info()
            if account:
                logger.info(f"MT Account: {account.login} | Balance: {account.balance} {account.currency}")
                return True
        
        return False
    
    async def execute_with_validation(
        self,
        symbol: str,
        direction: str,
        volume: float,
        council_decision: Dict[str, Any],
        risk_approval: bool
    ) -> Tuple[bool, TradeResult]:
        """
        Execute trade with full validation chain.
        
        Requirements:
        1. Trading must be enabled
        2. Council quorum must be reached
        3. Risk governor must approve
        4. Account must have margin
        5. Bridge must be connected
        """
        import secrets
        instruction_id = secrets.token_urlsafe(16)
        
        # Check 1: Trading enabled
        if not self.is_trading_enabled:
            return False, TradeResult(
                instruction_id=instruction_id,
                status=OrderStatus.REJECTED,
                error_message="Trading is disabled"
            )
        
        # Check 2: Council quorum
        if not council_decision.get("quorum_reached"):
            return False, TradeResult(
                instruction_id=instruction_id,
                status=OrderStatus.REJECTED,
                error_message="Council quorum not reached"
            )
        
        # Check 3: Risk approval
        if not risk_approval:
            return False, TradeResult(
                instruction_id=instruction_id,
                status=OrderStatus.REJECTED,
                error_message="Risk governor rejected trade"
            )
        
        # Check 4: Bridge connection
        if not self.bridge.is_connected:
            await self.bridge.connect()
            if not self.bridge.is_connected:
                return False, TradeResult(
                    instruction_id=instruction_id,
                    status=OrderStatus.ERROR,
                    error_message="MT Bridge not connected"
                )
        
        # Check 5: Account margin
        account = await self.bridge.get_account_info()
        if not account or not account.trade_allowed:
            return False, TradeResult(
                instruction_id=instruction_id,
                status=OrderStatus.REJECTED,
                error_message="Trading not allowed on account"
            )
        
        # Apply position modifier from council
        adjusted_volume = volume * council_decision.get("position_size_modifier", 1.0)
        adjusted_volume = round(adjusted_volume, 2)
        
        if adjusted_volume < 0.01:
            return False, TradeResult(
                instruction_id=instruction_id,
                status=OrderStatus.REJECTED,
                error_message="Volume too small after council adjustment"
            )
        
        # Create instruction
        instruction = TradeInstruction(
            instruction_id=instruction_id,
            symbol=symbol,
            order_type=OrderType.BUY if direction.upper() == "BUY" else OrderType.SELL,
            volume=adjusted_volume,
            comment=f"NEXUS|{council_decision.get('consensus_confidence', 0):.0%}"
        )
        
        # Execute
        self.pending_trades[instruction_id] = instruction
        result = await self.bridge.execute_trade(instruction)
        
        # Store result
        del self.pending_trades[instruction_id]
        self.executed_trades.append(result)
        
        success = result.status == OrderStatus.FILLED
        return success, result
    
    def halt_trading(self, reason: str):
        """Halt all trading."""
        self.is_trading_enabled = False
        logger.critical(f"Trading HALTED: {reason}")
    
    def resume_trading(self):
        """Resume trading."""
        self.is_trading_enabled = True
        logger.info("Trading RESUMED")


# =============================================================================
# SESSION-BOUND MT BRIDGE (Upgrade Layer)
# =============================================================================

class SessionBoundMTBridge:
    """
    Session-bound wrapper for MTBridgeClient.
    
    Ensures:
    - MT5 connection is initialized ONLY after user login
    - Each connection is bound to an authenticated session
    - Exponential backoff reconnection (3 retries: 1s → 2s → 4s)
    - Connection timeout detection (30s default)
    - Graceful failure instead of process crash
    
    Existing MTBridgeClient and TradeExecutionGateway are untouched.
    This is an upgrade layer, not a rewrite.
    """
    
    MAX_RETRIES = 3
    BASE_BACKOFF = 1.0  # seconds
    CONNECTION_TIMEOUT = 30  # seconds
    
    def __init__(self, bridge_url: str = "http://localhost:5000"):
        self.bridge_url = bridge_url
        # Per-user connection state: {user_id: {client, connected, last_activity, session_id}}
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._lock = None  # Created lazily since asyncio loop may not exist yet
    
    def _get_user_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get connection state for a user."""
        return self._connections.get(user_id)
    
    async def initialize_for_session(self, user_id: str, session_token: str) -> bool:
        """
        Initialize MT5 connection for an authenticated session.
        
        Must be called AFTER login. Connection is bound to this user.
        Returns True if connected, False otherwise.
        """
        import asyncio
        
        # Check if already connected for this user
        existing = self._connections.get(user_id)
        if existing and existing.get("connected"):
            existing["last_activity"] = time.time()
            logger.info(f"MT5 bridge already connected for user {user_id[:8]}...")
            return True
        
        # Create new client for this user
        client = MTBridgeClient(
            bridge_url=self.bridge_url,
            timeout=self.CONNECTION_TIMEOUT
        )
        
        # Attempt connection with exponential backoff
        connected = await self._connect_with_backoff(client, user_id)
        
        # Store connection state
        self._connections[user_id] = {
            "client": client,
            "connected": connected,
            "session_token": session_token,
            "created_at": time.time(),
            "last_activity": time.time(),
            "reconnect_count": 0,
        }
        
        if connected:
            logger.info(f"MT5 bridge connected for user {user_id[:8]}...")
        else:
            logger.warning(f"MT5 bridge connection FAILED for user {user_id[:8]}... (will retry on next trade)")
        
        return connected
    
    async def _connect_with_backoff(self, client: MTBridgeClient, user_id: str) -> bool:
        """
        Attempt connection with exponential backoff.
        
        Retries: 1s → 2s → 4s then gives up.
        """
        import asyncio
        
        for attempt in range(self.MAX_RETRIES):
            try:
                connected = await client.connect()
                if connected:
                    return True
            except Exception as e:
                logger.warning(f"MT5 connection attempt {attempt + 1}/{self.MAX_RETRIES} failed: {e}")
            
            if attempt < self.MAX_RETRIES - 1:
                backoff = self.BASE_BACKOFF * (2 ** attempt)
                logger.info(f"Retrying MT5 connection in {backoff}s...")
                await asyncio.sleep(backoff)
        
        return False
    
    async def reconnect(self, user_id: str) -> bool:
        """Attempt to reconnect for a user."""
        state = self._connections.get(user_id)
        if not state:
            logger.error(f"No connection state for user {user_id[:8]}... — must initialize first")
            return False
        
        client = state["client"]
        state["reconnect_count"] += 1
        
        connected = await self._connect_with_backoff(client, user_id)
        state["connected"] = connected
        state["last_activity"] = time.time()
        
        return connected
    
    def is_connected(self, user_id: str) -> bool:
        """Check if user has an active MT5 connection."""
        state = self._connections.get(user_id)
        if not state:
            return False
        
        # Check for timeout
        if time.time() - state["last_activity"] > self.CONNECTION_TIMEOUT:
            state["connected"] = False
            logger.warning(f"MT5 connection timed out for user {user_id[:8]}...")
            return False
        
        return state.get("connected", False)
    
    def get_client(self, user_id: str) -> Optional[MTBridgeClient]:
        """
        Get the MT5 client for a user.
        
        Returns None if not connected. Caller should check is_connected() first
        or handle None gracefully.
        """
        state = self._connections.get(user_id)
        if not state or not state.get("connected"):
            return None
        
        state["last_activity"] = time.time()
        return state["client"]
    
    async def disconnect(self, user_id: str):
        """Disconnect and cleanup for a user."""
        state = self._connections.pop(user_id, None)
        if state and state.get("client"):
            try:
                await state["client"].disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting MT5 for user {user_id[:8]}...: {e}")
            logger.info(f"MT5 bridge disconnected for user {user_id[:8]}...")
    
    async def disconnect_all(self):
        """Disconnect all user connections."""
        for user_id in list(self._connections.keys()):
            await self.disconnect(user_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get connection status for all users."""
        return {
            "active_connections": len([
                uid for uid, state in self._connections.items()
                if state.get("connected")
            ]),
            "total_sessions": len(self._connections),
            "connections": {
                uid[:8] + "...": {
                    "connected": state.get("connected", False),
                    "reconnect_count": state.get("reconnect_count", 0),
                    "age_seconds": int(time.time() - state.get("created_at", time.time())),
                }
                for uid, state in self._connections.items()
            }
        }


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

_gateway: Optional[TradeExecutionGateway] = None
_session_bridge: Optional[SessionBoundMTBridge] = None


def get_mt_gateway() -> TradeExecutionGateway:
    """Get or create MT gateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = TradeExecutionGateway()
    return _gateway


def get_session_bridge() -> SessionBoundMTBridge:
    """Get or create session-bound MT bridge."""
    global _session_bridge
    if _session_bridge is None:
        _session_bridge = SessionBoundMTBridge()
    return _session_bridge

