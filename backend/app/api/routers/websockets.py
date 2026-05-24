from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError
from app.core.security import SECRET_KEY, ALGORITHM
from app.api.ws_manager import manager

router = APIRouter(tags=["Real-Time"])

@router.websocket("/ws/events/{org_id}")
async def websocket_endpoint(websocket: WebSocket, org_id: int, token: str = Query(...)):
    # 1. Authenticate the WebSocket connection using the JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_org_id = payload.get("org_id")
        
        # Ensure the user belongs to the organization they are trying to listen to
        if token_org_id != org_id:
            await websocket.close(code=1008) # Policy Violation
            return
    except JWTError:
        await websocket.close(code=1008)
        return

    # 2. Connect the client
    await manager.connect(websocket, org_id)
    try:
        while True:
            # Keep the connection open and listen for client disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, org_id)