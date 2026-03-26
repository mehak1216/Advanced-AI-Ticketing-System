from typing import Set
from fastapi import WebSocket

ws_clients: Set[WebSocket] = set()

async def register(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)

async def unregister(ws: WebSocket):
    ws_clients.discard(ws)

async def broadcast_event(payload: dict):
    dead = []
    for ws in ws_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_clients.discard(ws)
