from __future__ import annotations

from dataclasses import dataclass
from shlex import quote

from acp_core.agents.types import (
    AgentCapabilities,
    AgentLaunchPlan,
    AgentRequest,
    CodingAgentAdapterProtocol,
)
from acp_core.settings import settings

_DEPRECATED_DEFAULT_TEMPLATE = (
    "export ACP_RUNTIME_HOME={acp_runtime_home}; "
    "codex --dangerously-bypass-approvals-and-sandbox exec - < {prompt_file}"
)


class CodexAgentAdapter:
    name = "codex"

    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            supports_model=True,
            native_resume=True,
            permission_modes=frozenset({"danger-full-access"}),
            output_modes=frozenset({"json", "stream-json"}),
            supports_streaming_json=True,
            supports_allowed_tools=True,
            supports_disallowed_tools=True,
            supports_max_turns=True,
            specialized_modes=frozenset({"review", "verify"}),
        )

    def build_launch_plan(self, request: AgentRequest) -> AgentLaunchPlan:
        template = settings.bootstrap_agent_command_template
        if template and template != _DEPRECATED_DEFAULT_TEMPLATE:
            legacy_command = template.format(
                prompt_file=_shell_join([str(request.prompt_file)]),
                acp_runtime_home=_shell_join([str(settings.runtime_home)]),
            )
            # TODO(bootstrap-agents): remove ACP_BOOTSTRAP_AGENT_COMMAND_TEMPLATE bridge after
            # operators migrate to adapter-native request fields.
            return AgentLaunchPlan(
                argv=["bash", "-lc", legacy_command],
                env={},
                display_command=legacy_command,
                metadata={"legacy_template_bridge": True, "agent": self.name},
            )

        argv = ["codex"]
        if request.permissions == "danger-full-access":
            argv.append("--dangerously-bypass-approvals-and-sandbox")
        if request.model:
            argv.extend(["--model", request.model])
        if request.output:
            argv.extend(["--output-format", request.output])
        argv.extend(["exec", "-"])

        return AgentLaunchPlan(
            argv=argv,
            env={"ACP_RUNTIME_HOME": str(settings.runtime_home)},
            display_command=f"codex {' '.join(argv[1:])} < {request.prompt_file}",
            metadata={
                "agent": self.name,
                "task_kind": request.task_kind,
                "stdin_file": str(request.prompt_file),
            },
            resume_hint="Use `codex resume` with the previous session context when continuing kickoff.",
        )


class ClaudeCodeAgentAdapter:
    name = "claude-code"

    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            supports_model=True,
            native_resume=True,
        )

    def build_launch_plan(self, request: AgentRequest) -> AgentLaunchPlan:
        argv = ["claude", "--print"]
        if request.model:
            argv.extend(["--model", request.model])
        return AgentLaunchPlan(
            argv=argv,
            env={"ACP_RUNTIME_HOME": str(settings.runtime_home)},
            display_command=f"claude {' '.join(argv[1:])} < {request.prompt_file}",
            metadata={
                "agent": self.name,
                "task_kind": request.task_kind,
                "stdin_file": str(request.prompt_file),
            },
            resume_hint="Use Claude Code conversation resume in the same working directory.",
        )


class AiderAgentAdapter:
    name = "aider"

    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            supports_model=True,
            native_resume=True,
        )

    def build_launch_plan(self, request: AgentRequest) -> AgentLaunchPlan:
        argv = ["aider", "--message-file", str(request.prompt_file)]
        if request.model:
            argv.extend(["--model", request.model])
        return AgentLaunchPlan(
            argv=argv,
            env={"ACP_RUNTIME_HOME": str(settings.runtime_home)},
            display_command=_shell_join(argv),
            metadata={"agent": self.name, "task_kind": request.task_kind},
            resume_hint="Use `aider --resume` inside the same checkout to continue kickoff.",
        )


@dataclass(frozen=True)
class AgentRegistry:
    adapters: dict[str, CodingAgentAdapterProtocol]
    aliases: dict[str, str]

    @classmethod
    def default(cls) -> AgentRegistry:
        return cls(
            adapters={
                "codex": CodexAgentAdapter(),
                "claude_code": ClaudeCodeAgentAdapter(),
                "aider": AiderAgentAdapter(),
            },
            aliases={
                "codex": "codex",
                "claude": "claude_code",
                "claude-code": "claude_code",
                "claude_code": "claude_code",
                "aider": "aider",
            },
        )

    def canonical_key(self, agent_name: str) -> str:
        normalized = agent_name.strip().lower()
        return self.aliases.get(normalized, normalized)

    def resolve(self, agent_name: str) -> CodingAgentAdapterProtocol:
        canonical = self.canonical_key(agent_name)
        adapter = self.adapters.get(canonical)
        if adapter is None:
            raise ValueError(
                f"Unsupported bootstrap agent '{agent_name}'. Supported agents: {', '.join(sorted(self.adapters))}"
            )
        return adapter


def resolve_coding_agent_adapter(
    agent_name: str | None,
    *,
    registry: AgentRegistry | None = None,
    default_agent: str | None = None,
):
    resolved_registry = registry or AgentRegistry.default()
    resolved_agent = (
        (agent_name or default_agent or settings.default_agent).strip().lower()
    )
    return resolved_registry.resolve(resolved_agent)


def _shell_join(parts: list[str]) -> str:
    return " ".join(quote(part) for part in parts)
