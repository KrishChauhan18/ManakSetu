import asyncio
import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Map scan_id (str) -> List of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Latest known status cache per scan_id
        self.status_cache: Dict[str, Dict[str, Any]] = {}

    async def connect(self, scan_id: str, websocket: WebSocket):
        await websocket.accept()
        if scan_id not in self.active_connections:
            self.active_connections[scan_id] = []
        self.active_connections[scan_id].append(websocket)
        logger.info(f"WebSocket client connected to scan {scan_id}")

        # Send latest known status immediately if available
        if scan_id in self.status_cache:
            try:
                await websocket.send_json(self.status_cache[scan_id])
            except Exception:
                pass

    def disconnect(self, scan_id: str, websocket: WebSocket):
        if scan_id in self.active_connections:
            if websocket in self.active_connections[scan_id]:
                self.active_connections[scan_id].remove(websocket)
            if not self.active_connections[scan_id]:
                del self.active_connections[scan_id]
        logger.info(f"WebSocket client disconnected from scan {scan_id}")

    async def broadcast_status(self, scan_id: str, stage: str, progress_pct: int, message: str = ""):
        payload = {
            "scan_id": scan_id,
            "stage": stage,
            "progress_pct": progress_pct,
            "message": message
        }
        self.status_cache[scan_id] = payload

        if scan_id in self.active_connections:
            dead_sockets = []
            for ws in self.active_connections[scan_id]:
                try:
                    await ws.send_json(payload)
                except Exception:
                    dead_sockets.append(ws)
            for dead in dead_sockets:
                self.disconnect(scan_id, dead)

ws_manager = WebSocketManager()
