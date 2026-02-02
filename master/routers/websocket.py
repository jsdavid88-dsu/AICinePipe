from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..websocket.connection_manager import manager

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Worker로부터 메시지 수신 (Heartbeat, Job Status 등)
            data = await websocket.receive_text()
            # TODO: Handle messages (JSON parse -> Action)
            print(f"Received from {client_id}: {data}")
            
            # Echo for test
            await manager.send_personal_message({"type": "echo", "data": data}, client_id)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket Error on {client_id}: {e}")
        manager.disconnect(client_id)
