from __future__ import annotations

from acp_core.runtime import RuntimeLaunchSpec, TmuxRuntimeAdapter


def test_resolve_spawn_command_includes_stdin_redirection_from_adapter_metadata() -> None:
    runtime = object.__new__(TmuxRuntimeAdapter)

    launch_spec = RuntimeLaunchSpec(
        argv=["codex", "exec", "-"],
        env={"ACP_RUNTIME_HOME": "/tmp/runtime"},
        display_command="codex exec - < /tmp/prompt.md",
        working_directory="/tmp/work",
        adapter_metadata={
            "agent": "codex",
            "stdin_file": "/tmp/prompt.md",
        },
    )

    command = runtime._resolve_spawn_command(
        profile="executor", launch_spec=launch_spec, command=None
    )

    assert command == "env ACP_RUNTIME_HOME=/tmp/runtime codex exec - < /tmp/prompt.md"


def test_resolve_spawn_command_does_not_add_stdin_redirection_without_stdin_file() -> None:
    runtime = object.__new__(TmuxRuntimeAdapter)

    launch_spec = RuntimeLaunchSpec(
        argv=["codex", "exec", "-"],
        env={"ACP_RUNTIME_HOME": "/tmp/runtime"},
        display_command="codex exec -",
        working_directory="/tmp/work",
        adapter_metadata={"agent": "codex"},
    )

    command = runtime._resolve_spawn_command(
        profile="executor", launch_spec=launch_spec, command=None
    )

    assert command == "env ACP_RUNTIME_HOME=/tmp/runtime codex exec -"
