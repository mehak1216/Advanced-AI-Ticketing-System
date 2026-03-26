from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.ws_service import register, unregister

router = APIRouter()

@router.websocket("/tickets")
async def tickets_ws(websocket: WebSocket):
    await register(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await unregister(websocket)
