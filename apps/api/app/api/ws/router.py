from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws")
async def websocket_events(websocket: WebSocket) -> None:
    project_id = websocket.query_params.get("project_id")
    task_id = websocket.query_params.get("task_id")
    session_id = websocket.query_params.get("session_id")
    hub = websocket.app.state.ws_hub
    subscription_id, queue = await hub.connect(
        websocket,
        project_id=project_id,
        task_id=task_id,
        session_id=session_id,
    )
    await websocket.send_json(
        {
            "type": "system.connected",
            "message": "📡 Live mutation streaming connected.",
            "project_id": project_id,
            "task_id": task_id,
            "session_id": session_id,
        }
    )
    try:
        while True:
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=20)
            except TimeoutError:
                await websocket.send_json({"type": "system.ping"})
                continue
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        await hub.disconnect(subscription_id)
