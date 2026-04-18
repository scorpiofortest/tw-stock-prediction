"""WebSocket endpoint for real-time updates."""

from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from core.ws_manager import ws_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint.
    Client messages:
      {"action": "subscribe", "stock_id": "2330"}
      {"action": "unsubscribe", "stock_id": "2330"}
      {"action": "ping"}
    Server messages:
      quote_update, signal_update, prediction_created, prediction_verified, pong
    """
    conn_id = await ws_manager.connect(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "connection_id": conn_id,
            "server_time": datetime.now().isoformat(),
        })

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                stock_id = data.get("stock_id")
                if stock_id:
                    await ws_manager.subscribe(conn_id, stock_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "stock_id": stock_id,
                    })

            elif action == "unsubscribe":
                stock_id = data.get("stock_id")
                if stock_id:
                    await ws_manager.unsubscribe(conn_id, stock_id)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "stock_id": stock_id,
                    })

            elif action == "ping":
                ws_manager.record_pong(conn_id)
                await websocket.send_json({
                    "type": "pong",
                    "server_time": datetime.now().isoformat(),
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown action: {action}",
                })

    except WebSocketDisconnect:
        await ws_manager.disconnect(conn_id)
    except Exception as e:
        logger.error(f"WebSocket error for {conn_id}: {e}")
        await ws_manager.disconnect(conn_id)
