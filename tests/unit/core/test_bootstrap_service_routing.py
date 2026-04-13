from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from acp_core.agents.types import AgentCapabilities, AgentLaunchPlan, AgentRequest
from acp_core.services.base_service import ServiceContext
from acp_core.services.bootstrap_service import BootstrapService
from acp_core.schemas import ProjectBootstrapCreate, StackPreset


class FakeAdapter:
    name = "codex"

    def __init__(self) -> None:
        self.requests: list[AgentRequest] = []

    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(supports_model=True, native_resume=True)

    def build_launch_plan(self, request: AgentRequest) -> AgentLaunchPlan:
        self.requests.append(request)
        return AgentLaunchPlan(
            argv=["codex", "exec", "-"],
            env={"ACP_RUNTIME_HOME": "/runtime"},
            display_command=f"codex exec - < {request.prompt_file}",
            metadata={"agent": "codex", "task_kind": request.task_kind},
        )


class FakeRegistry:
    def __init__(self, adapter: FakeAdapter) -> None:
        self.adapter = adapter

    def canonical_key(self, agent_name: str) -> str:
        return agent_name.replace("-", "_").lower()

    def resolve(self, agent_name: str) -> FakeAdapter:
        return self.adapter


class FakeSessionService:
    last_payload = None

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def spawn_session(self, payload):
        FakeSessionService.last_payload = payload
        return SimpleNamespace(id="sess-1", runtime_metadata={"existing": True})


def _payload(agent_name: str | None = None) -> ProjectBootstrapCreate:
    return ProjectBootstrapCreate(
        name="Demo",
        description="desc",
        repo_path="/tmp/repo",
        initialize_repo=False,
        stack_preset=StackPreset.FASTAPI_SERVICE,
        initial_prompt="Start planning",
        use_worktree=False,
        agent_name=agent_name,
    )


def test_build_agent_request_uses_configured_kickoff_agent() -> None:
    context = ServiceContext(db=MagicMock(), actor_type="human", actor_name="tester")
    adapter = FakeAdapter()
    service = BootstrapService(context=context, runtime=MagicMock(), agent_registry=FakeRegistry(adapter))

    state = service.BootstrapState(payload=_payload(agent_name="claude-code"), repo_path=Path("/tmp/repo"))
    state.execution_path = Path("/tmp/repo")
    state.project = SimpleNamespace(id="proj-1")
    state.kickoff_task = SimpleNamespace(id="task-1")

    request = service._build_agent_request(state)

    assert request.agent_name == "claude_code"
    assert request.task_kind == "kickoff"
    assert request.metadata == {"project_id": "proj-1", "task_id": "task-1"}


def test_launch_kickoff_session_passes_launch_plan_and_sets_agent_metadata(monkeypatch) -> None:
    context = ServiceContext(db=MagicMock(), actor_type="human", actor_name="tester")
    adapter = FakeAdapter()
    service = BootstrapService(context=context, runtime=MagicMock(), agent_registry=FakeRegistry(adapter))

    monkeypatch.setattr("acp_core.services.bootstrap_service.SessionService", FakeSessionService)
    service._write_project_local_files = MagicMock()

    state = service.BootstrapState(payload=_payload(agent_name="codex"), repo_path=Path("/tmp/repo"))
    state.project = SimpleNamespace(id="proj-1", name="Demo")
    state.repository = SimpleNamespace(id="repo-1")
    state.kickoff_task = SimpleNamespace(id="task-1")
    state.kickoff_worktree = None
    state.execution_path = Path("/tmp/repo")

    service._launch_kickoff_session(state)

    assert FakeSessionService.last_payload is not None
    assert FakeSessionService.last_payload.launch_spec.argv == ["codex", "exec", "-"]
    assert FakeSessionService.last_payload.launch_spec.env == {"ACP_RUNTIME_HOME": "/runtime"}
    assert state.session.runtime_metadata["agent_request"]["agent_name"] == "codex"
    assert state.session.runtime_metadata["agent_launch_plan"]["metadata"] == {
        "agent": "codex",
        "task_kind": "kickoff",
    }
