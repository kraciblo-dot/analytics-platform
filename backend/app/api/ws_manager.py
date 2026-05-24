from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        # Maps an organization_id to a list of active WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, org_id: int):
        await websocket.accept()
        if org_id not in self.active_connections:
            self.active_connections[org_id] = []
        self.active_connections[org_id].append(websocket)

    def disconnect(self, websocket: WebSocket, org_id: int):
        if org_id in self.active_connections:
            self.active_connections[org_id].remove(websocket)

    async def broadcast_to_org(self, message: dict, org_id: int):
        """Pushes a JSON message to all connected clients in a specific organization"""
        if org_id in self.active_connections:
            for connection in self.active_connections[org_id]:
                await connection.send_text(json.dumps(message))

manager = ConnectionManager()