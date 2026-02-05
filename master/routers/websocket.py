from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from ..websocket.connection_manager import manager
from ..services.worker_manager import WorkerManager
from ..dependencies import get_worker_manager
import json

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, worker_manager: WorkerManager = Depends(get_worker_manager)):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                
                if msg.get("type") == "heartbeat":
                    # Delegate parsing to WorkerManager (separation of concerns)
                    client_ip = websocket.client.host if websocket.client else "127.0.0.1"
                    worker_node = worker_manager.parse_heartbeat_message(client_id, msg, client_ip)
                    worker_manager.register_worker(worker_node)
                    
            except json.JSONDecodeError:
                pass
                
            print(f"Received from {client_id}: {data}")
            await manager.send_personal_message({"type": "echo", "data": data}, client_id)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket Error on {client_id}: {e}")
        manager.disconnect(client_id)

