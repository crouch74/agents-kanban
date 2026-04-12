from __future__ import annotations

from pathlib import Path
from typing import Protocol

from acp_core.runtime import RuntimeLaunchSpec, RuntimeSessionInfo, RuntimeSessionSummary, TmuxRuntimeAdapter


class RuntimeAdapterProtocol(Protocol):
    def spawn_session(
        self,
        *,
        session_name: str,
        working_directory: Path,
        profile: str,
        launch_spec: RuntimeLaunchSpec | None = None,
        command: str | None = None,
    ) -> RuntimeSessionInfo: ...

    def session_exists(self, session_name: str) -> bool: ...

    def capture_tail(self, session_name: str, *, lines: int = 120) -> str: ...

    def terminate_session(self, session_name: str) -> None: ...

    def is_session_active(self, session_name: str) -> bool: ...

    def list_sessions(self, *, prefix: str | None = None) -> list[RuntimeSessionSummary]: ...


DefaultRuntimeAdapter = TmuxRuntimeAdapter
