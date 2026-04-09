from __future__ import annotations

from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/ws")
async def websocket_events(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json(
        {
            "type": "system.message",
            "message": "📡 WebSocket support is online. Live session streaming lands in the next phase.",
        }
    )
    await websocket.close()

