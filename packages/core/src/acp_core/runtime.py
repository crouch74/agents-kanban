from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shlex import quote

from libtmux import Server


DEFAULT_PROFILE_COMMANDS: dict[str, str] = {
    "executor": "printf '🤖 Executor session ready\\n'; exec ${SHELL:-/bin/zsh} -l",
    "reviewer": "printf '🤖 Reviewer session ready\\n'; exec ${SHELL:-/bin/zsh} -l",
    "verifier": "printf '🤖 Verifier session ready\\n'; exec ${SHELL:-/bin/zsh} -l",
    "research": "printf '🤖 Research session ready\\n'; exec ${SHELL:-/bin/zsh} -l",
    "docs": "printf '🤖 Documentation session ready\\n'; exec ${SHELL:-/bin/zsh} -l",
}


@dataclass(frozen=True)
class RuntimeSessionInfo:
    session_name: str
    pane_id: str
    window_name: str
    working_directory: str
    command: str


class TmuxRuntimeAdapter:
    def __init__(self) -> None:
        self.server = Server()

    def spawn_session(
        self,
        *,
        session_name: str,
        working_directory: Path,
        profile: str,
        command: str | None = None,
    ) -> RuntimeSessionInfo:
        session = self.server.find_where({"session_name": session_name})
        resolved_command = command or DEFAULT_PROFILE_COMMANDS.get(profile, DEFAULT_PROFILE_COMMANDS["executor"])

        if session is None:
            session = self.server.new_session(
                session_name=session_name,
                attach=False,
                kill_session=False,
                start_directory=str(working_directory),
                window_name="main",
            )
            pane = session.attached_window.attached_pane
            pane.send_keys(resolved_command, enter=True)
        else:
            pane = session.attached_window.attached_pane

        return RuntimeSessionInfo(
            session_name=session.get("session_name"),
            pane_id=pane.get("pane_id"),
            window_name=session.attached_window.get("window_name"),
            working_directory=str(working_directory),
            command=resolved_command,
        )

    def session_exists(self, session_name: str) -> bool:
        return self.server.find_where({"session_name": session_name}) is not None

    def capture_tail(self, session_name: str, *, lines: int = 120) -> str:
        session = self.server.find_where({"session_name": session_name})
        if session is None:
            raise ValueError("Runtime session not found")
        pane = session.attached_window.attached_pane
        content = pane.capture_pane(start=-lines)
        return "\n".join(content)

    def terminate_session(self, session_name: str) -> None:
        session = self.server.find_where({"session_name": session_name})
        if session is not None:
            session.kill_session()


def safe_tmux_name(raw_name: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in raw_name.lower())
    return cleaned.strip("-_")[:48] or "acp-session"


def shell_join(parts: list[str]) -> str:
    return " ".join(quote(part) for part in parts)
