import asyncio
import json
import logging
from typing import Dict, List, Set, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("nexus.ws_manager")

class ConnectionManager:
    """Manages WebSocket connections for NEXUS."""
    
    def __init__(self):
        # Active connections: {page_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Subscriptions: {symbol: {connection_ids}}
        self.subscriptions: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept a new connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"New NEXUS connection: {connection_id}")
        
    def disconnect(self, connection_id: str):
        """Remove a connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            # Clean up subscriptions
            for symbol in list(self.subscriptions.keys()):
                if connection_id in self.subscriptions[symbol]:
                    self.subscriptions[symbol].remove(connection_id)
            logger.info(f"NEXUS connection terminated: {connection_id}")

    async def subscribe(self, connection_id: str, symbols: List[str]):
        """Subscribe a connection to symbols."""
        for symbol in symbols:
            symbol = symbol.upper()
            if symbol not in self.subscriptions:
                self.subscriptions[symbol] = set()
            self.subscriptions[symbol].add(connection_id)
        logger.info(f"Connection {connection_id} subscribed to {symbols}")

    async def broadcast_status(self, status: Dict[str, Any]):
        """Broadcast system status to ALL connections."""
        payload = {
            "type": "STATUS",
            "data": status
        }
        await self._broadcast(payload)

    async def broadcast_tick(self, tick_data: Dict[str, Any]):
        """Broadcast tick data to SUBSCRIBED connections only."""
        symbol = tick_data.get("symbol")
        if not symbol:
            return
            
        payload = {
            "type": "TICK",
            "data": tick_data
        }
        
        target_ids = self.subscriptions.get(symbol.upper(), set())
        for conn_id in target_ids:
            if conn_id in self.active_connections:
                try:
                    await self.active_connections[conn_id].send_text(json.dumps(payload))
                except Exception as e:
                    logger.error(f"Failed to send tick to {conn_id}: {e}")

    async def _broadcast(self, message: Dict[str, Any]):
        """Internal broadcast to all active connections."""
        json_msg = json.dumps(message)
        disconnected = []
        for conn_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json_msg)
            except Exception:
                disconnected.append(conn_id)
        
        for conn_id in disconnected:
            self.disconnect(conn_id)

# Global Instance
ws_manager = ConnectionManager()

def get_ws_manager():
    return ws_manager
