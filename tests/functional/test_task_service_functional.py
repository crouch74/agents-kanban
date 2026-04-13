from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from acp_core.constants import DEFAULT_BOARD_COLUMNS
from acp_core.models import AgentSession, Base, Board, BoardColumn, Project
from acp_core.runtime import RuntimeSessionInfo
from acp_core.schemas import TaskCheckCreate, TaskCreate, TaskPatch
from acp_core.services.base_service import ServiceContext
from acp_core.services.task_service import TaskService


class FakeRuntime:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, str]] = {}

    def spawn_session(
        self,
        *,
        session_name: str,
        working_directory: Path,
        profile: str,
        launch_spec=None,
        command: str | None = None,
    ) -> RuntimeSessionInfo:
        self.sessions[session_name] = {
            "working_directory": str(working_directory),
            "command": launch_spec.display_command if launch_spec else (command or profile),
        }
        return RuntimeSessionInfo(
            session_name=session_name,
            pane_id="%1",
            window_name="main",
            working_directory=str(launch_spec.working_directory) if launch_spec else str(working_directory),
            command=launch_spec.display_command if launch_spec else (command or profile),
        )

    def session_exists(self, session_name: str) -> bool:
        return session_name in self.sessions

    def is_session_active(self, session_name: str) -> bool:
        return session_name in self.sessions

    def list_sessions(self, *, prefix: str | None = None):
        names = sorted(self.sessions)
        if prefix is not None:
            names = [name for name in names if name.startswith(prefix)]
        return [
            type(
                "RuntimeSessionSummary",
                (),
                {"session_name": name, "window_name": "main"},
            )()
            for name in names
        ]


@pytest.fixture
def service_context(monkeypatch: pytest.MonkeyPatch) -> ServiceContext:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()

    project = Project(name="Functional Task Flow", slug="functional-task-flow")
    board = Board(project=project, name="Main Board")
    session.add(project)
    session.add(board)
    session.flush()
    for column_data in DEFAULT_BOARD_COLUMNS:
        session.add(BoardColumn(board_id=board.id, **column_data))
    session.commit()

    fake_runtime = FakeRuntime()
    monkeypatch.setattr(
        "acp_core.services.session_service.DefaultRuntimeAdapter",
        lambda: fake_runtime,
    )
    monkeypatch.setattr(
        "acp_core.services.waiting_service.DefaultRuntimeAdapter",
        lambda: fake_runtime,
    )
    monkeypatch.setattr(
        "acp_core.services.system_service.DefaultRuntimeAdapter",
        lambda: fake_runtime,
    )

    context = ServiceContext(
        db=session,
        actor_type="human",
        actor_name="functional-tests",
        runtime=fake_runtime,
    )
    context.project_id = project.id  # type: ignore[attr-defined]
    return context


def test_task_service_facade_runs_parent_subtree_sequence(service_context: ServiceContext) -> None:
    service = TaskService(service_context)
    project_id = service_context.project_id  # type: ignore[attr-defined]

    parent = service.create_task(
        TaskCreate(
            project_id=project_id,
            title="Parent task",
            description="Verify the whole feature at the end.",
            board_column_key="backlog",
        )
    )
    subtask_one = service.create_task(
        TaskCreate(
            project_id=project_id,
            title="Subtask one",
            description="Implement the first slice.",
            parent_task_id=parent.id,
            board_column_key="backlog",
        )
    )
    subtask_two = service.create_task(
        TaskCreate(
            project_id=project_id,
            title="Subtask two",
            description="Implement the second slice.",
            parent_task_id=parent.id,
            board_column_key="backlog",
        )
    )

    service.patch_task(parent.id, TaskPatch(workflow_state="ready"))

    sessions = list(
        service_context.db.scalars(
            select(AgentSession).order_by(AgentSession.created_at.asc())
        )
    )
    assert len(sessions) == 1
    assert sessions[0].task_id == subtask_one.id
    assert sessions[0].profile == "executor"

    service.patch_task(subtask_one.id, TaskPatch(workflow_state="in_progress"))
    service.patch_task(subtask_one.id, TaskPatch(workflow_state="review"))
    service.add_check(
        subtask_one.id,
        TaskCheckCreate(
            check_type="verification",
            status="passed",
            summary="Subtask one complete.",
        ),
    )
    service.patch_task(subtask_one.id, TaskPatch(workflow_state="done"))

    sessions = list(
        service_context.db.scalars(
            select(AgentSession).order_by(AgentSession.created_at.asc())
        )
    )
    assert len(sessions) == 2
    assert sessions[1].task_id == subtask_two.id
    assert sessions[1].profile == "executor"


def test_task_service_facade_keeps_single_task_ready_behavior(service_context: ServiceContext) -> None:
    service = TaskService(service_context)
    project_id = service_context.project_id  # type: ignore[attr-defined]

    task = service.create_task(
        TaskCreate(
            project_id=project_id,
            title="Standalone task",
            description="Implement one isolated change.",
            board_column_key="backlog",
        )
    )

    service.patch_task(task.id, TaskPatch(workflow_state="ready"))

    sessions = list(
        service_context.db.scalars(
            select(AgentSession).order_by(AgentSession.created_at.asc())
        )
    )
    assert len(sessions) == 1
    assert sessions[0].task_id == task.id
    assert sessions[0].profile == "executor"
