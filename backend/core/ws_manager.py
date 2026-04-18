"""WebSocket connection manager with per-stock subscription channels."""

import asyncio
from collections import defaultdict
from datetime import datetime
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


HEARTBEAT_INTERVAL = 30  # seconds
HEARTBEAT_TIMEOUT = 90   # seconds


class WebSocketManager:
    """Manages WebSocket connections, subscriptions, and broadcasting."""

    def __init__(self):
        # conn_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}
        # stock_id -> set of conn_ids
        self.stock_subscriptions: dict[str, set[str]] = defaultdict(set)
        # conn_id -> set of stock_ids
        self.connection_subscriptions: dict[str, set[str]] = defaultdict(set)
        # conn_id -> last pong time
        self.last_pong: dict[str, datetime] = {}
        self._heartbeat_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket) -> str:
        """Accept a WebSocket connection and return a unique connection ID."""
        await websocket.accept()
        conn_id = str(uuid4())
        self.active_connections[conn_id] = websocket
        self.last_pong[conn_id] = datetime.now()
        logger.info(f"WebSocket connected: {conn_id}")
        return conn_id

    async def disconnect(self, conn_id: str):
        """Disconnect and clean up all subscriptions for a connection."""
        for stock_id in self.connection_subscriptions.get(conn_id, set()).copy():
            self.stock_subscriptions[stock_id].discard(conn_id)
            if not self.stock_subscriptions[stock_id]:
                del self.stock_subscriptions[stock_id]
        self.connection_subscriptions.pop(conn_id, None)
        self.active_connections.pop(conn_id, None)
        self.last_pong.pop(conn_id, None)
        logger.info(f"WebSocket disconnected: {conn_id}")

    async def subscribe(self, conn_id: str, stock_id: str):
        """Subscribe a connection to a stock channel."""
        self.stock_subscriptions[stock_id].add(conn_id)
        self.connection_subscriptions[conn_id].add(stock_id)
        logger.debug(f"{conn_id} subscribed to {stock_id}")

    async def unsubscribe(self, conn_id: str, stock_id: str):
        """Unsubscribe a connection from a stock channel."""
        self.stock_subscriptions[stock_id].discard(conn_id)
        self.connection_subscriptions[conn_id].discard(stock_id)
        if not self.stock_subscriptions[stock_id]:
            del self.stock_subscriptions[stock_id]
        logger.debug(f"{conn_id} unsubscribed from {stock_id}")

    async def broadcast_to_stock(self, stock_id: str, message: dict):
        """Send a message to all connections subscribed to a stock."""
        conn_ids = self.stock_subscriptions.get(stock_id, set()).copy()
        dead = []
        for conn_id in conn_ids:
            ws = self.active_connections.get(conn_id)
            if ws:
                try:
                    await ws.send_json(message)
                except (WebSocketDisconnect, RuntimeError):
                    dead.append(conn_id)
        for conn_id in dead:
            await self.disconnect(conn_id)

    async def broadcast_all(self, message: dict):
        """Send a message to every active connection."""
        dead = []
        for conn_id, ws in list(self.active_connections.items()):
            try:
                await ws.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                dead.append(conn_id)
        for conn_id in dead:
            await self.disconnect(conn_id)

    def get_subscribed_stocks(self) -> set[str]:
        """Return the set of all stock IDs with active subscriptions."""
        return set(
            sid for sid, conns in self.stock_subscriptions.items() if conns
        )

    async def start_heartbeat(self):
        """Start the heartbeat loop as a background task."""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop_heartbeat(self):
        """Cancel the heartbeat task."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def _heartbeat_loop(self):
        """Periodically ping clients and clean up timed-out connections."""
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            now = datetime.now()
            dead = []
            for conn_id, ws in list(self.active_connections.items()):
                last = self.last_pong.get(conn_id, now)
                if (now - last).total_seconds() > HEARTBEAT_TIMEOUT:
                    dead.append(conn_id)
                    continue
                try:
                    await ws.send_json({"type": "ping", "server_time": now.isoformat()})
                except (WebSocketDisconnect, RuntimeError):
                    dead.append(conn_id)
            for conn_id in dead:
                await self.disconnect(conn_id)

    def record_pong(self, conn_id: str):
        """Record a pong response from a client."""
        self.last_pong[conn_id] = datetime.now()


# Global singleton
ws_manager = WebSocketManager()
