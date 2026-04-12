from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shlex import quote

from libtmux import Server


DEFAULT_PROFILE_COMMANDS: dict[str, str] = {
    "executor": "printf '🤖 Agent session initialized\\n🚀 Run `codex exec` to start an autonomous turn or types commands to explore.\\n'; exec ${SHELL:-/bin/zsh} -l",
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


@dataclass(frozen=True)
class RuntimeSessionSummary:
    session_name: str
    window_name: str
    is_active: bool = True


@dataclass(frozen=True)
class RuntimeLaunchSpec:
    argv: list[str]
    env: dict[str, str]
    display_command: str
    working_directory: str
    legacy_shell_command: str | None = None


class TmuxRuntimeAdapter:
    def __init__(self) -> None:
        import shutil
        tmux_bin = shutil.which("tmux")
        if not tmux_bin:
            # Common macOS paths if which fails
            for p in ["/usr/local/bin/tmux", "/opt/homebrew/bin/tmux", "/opt/local/bin/tmux"]:
                if Path(p).exists():
                    tmux_bin = p
                    break
        
        self.server = Server(tmux_executable=tmux_bin)
        if tmux_bin:
            import os
            bin_dir = str(Path(tmux_bin).parent)
            if bin_dir not in os.environ["PATH"]:
                os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"

    def spawn_session(
        self,
        *,
        session_name: str,
        working_directory: Path,
        profile: str,
        launch_spec: RuntimeLaunchSpec | None = None,
        command: str | None = None,
    ) -> RuntimeSessionInfo:
        session = self.server.find_where({"session_name": session_name})
        resolved_working_directory = Path(launch_spec.working_directory) if launch_spec else working_directory
        resolved_command = self._resolve_spawn_command(
            profile=profile,
            launch_spec=launch_spec,
            command=command,
        )

        if session is None:
            session = self.server.new_session(
                session_name=session_name,
                attach=False,
                kill_session=False,
                start_directory=str(resolved_working_directory),
                window_name="main",
            )
            pane = session.attached_window.attached_pane
            pane.send_keys(resolved_command, enter=True)
        else:
            pane = session.attached_window.attached_pane

        return RuntimeSessionInfo(
            session_name=str(session.session_name),
            pane_id=str(pane.pane_id),
            window_name=str(session.attached_window.window_name),
            working_directory=str(resolved_working_directory),
            command=resolved_command,
        )

    def _resolve_spawn_command(
        self,
        *,
        profile: str,
        launch_spec: RuntimeLaunchSpec | None,
        command: str | None,
    ) -> str:
        if launch_spec is not None:
            if launch_spec.legacy_shell_command:
                return launch_spec.legacy_shell_command

            command_tokens = [
                "env",
                *(f"{key}={value}" for key, value in launch_spec.env.items()),
                *launch_spec.argv,
            ]
            return shell_join(command_tokens)

        if command is not None:
            return command

        return DEFAULT_PROFILE_COMMANDS.get(profile, DEFAULT_PROFILE_COMMANDS["executor"])

    def session_exists(self, session_name: str) -> bool:
        return self.server.find_where({"session_name": session_name}) is not None

    def is_session_active(self, session_name: str) -> bool:
        session = self.server.find_where({"session_name": session_name})
        if session is None:
            return False
        
        pane = session.attached_window.attached_pane
        current_command = str(pane.pane_current_command)
        # If the command is just a common shell, we consider it "idle" (not active)
        # Note: 'exec''ing into a shell at the end of a turn is a common pattern here.
        if current_command in {"zsh", "bash", "sh", "fish", "tmux"}:
            return False
        return True

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

    def list_sessions(self, *, prefix: str | None = None) -> list[RuntimeSessionSummary]:
        sessions: list[RuntimeSessionSummary] = []
        for session in self.server.sessions:
            session_name = str(session.session_name)
            if prefix is not None and not session_name.startswith(prefix):
                continue
            sessions.append(
                RuntimeSessionSummary(
                    session_name=session_name,
                    window_name=str(session.attached_window.window_name),
                    is_active=self.is_session_active(session_name),
                )
            )
        return sessions


def safe_tmux_name(raw_name: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in raw_name.lower())
    return cleaned.strip("-_")[:48] or "acp-session"


def shell_join(parts: list[str]) -> str:
    return " ".join(quote(part) for part in parts)
