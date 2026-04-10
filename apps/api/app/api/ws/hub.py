from __future__ import annotations

import asyncio
from dataclasses import dataclass
from itertools import count
from typing import Any

from fastapi import WebSocket


@dataclass
class Subscription:
    websocket: WebSocket
    queue: asyncio.Queue[dict[str, Any]]
    project_id: str | None = None
    task_id: str | None = None
    session_id: str | None = None


class WebSocketHub:
    def __init__(self) -> None:
        self._subscriptions: dict[int, Subscription] = {}
        self._next_id = count(1)
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self) -> None:
        self._loop = asyncio.get_running_loop()

    async def connect(
        self,
        websocket: WebSocket,
        *,
        project_id: str | None = None,
        task_id: str | None = None,
        session_id: str | None = None,
    ) -> tuple[int, asyncio.Queue[dict[str, Any]]]:
        await websocket.accept()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        subscription = Subscription(
            websocket=websocket,
            queue=queue,
            project_id=project_id,
            task_id=task_id,
            session_id=session_id,
        )
        subscription_id = next(self._next_id)
        async with self._lock:
            self._subscriptions[subscription_id] = subscription
        return subscription_id, queue

    async def disconnect(self, subscription_id: int) -> None:
        async with self._lock:
            self._subscriptions.pop(subscription_id, None)

    def publish(self, payload: dict[str, Any]) -> None:
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._publish(payload), self._loop)

    async def _publish(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            subscriptions = list(self._subscriptions.values())
        for subscription in subscriptions:
            if not self._matches(subscription, payload):
                continue
            await subscription.queue.put(payload)

    def _matches(self, subscription: Subscription, payload: dict[str, Any]) -> bool:
        if subscription.project_id and payload.get("project_id") != subscription.project_id:
            return False
        if subscription.task_id and payload.get("task_id") != subscription.task_id:
            return False
        if subscription.session_id and payload.get("session_id") != subscription.session_id:
            return False
        return True
