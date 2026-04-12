from __future__ import annotations

from acp_mcp_server import server


def test_mcp_server_wrappers_delegate_to_handlers(monkeypatch) -> None:
    calls: list[tuple[str, tuple, dict]] = []

    class FakeModel:
        def __init__(self, payload: dict[str, object]) -> None:
            self.payload = payload

        def model_dump(self) -> dict[str, object]:
            return self.payload

    def recorder(name: str, result):
        def _wrapped(*args, **kwargs):
            calls.append((name, args, kwargs))
            return result

        return _wrapped

    monkeypatch.setattr(server.handlers, "project_list", recorder("project_list", [FakeModel({"id": "project-1"})]))
    monkeypatch.setattr(server.handlers, "project_get", recorder("project_get", {"id": "project-1"}))
    monkeypatch.setattr(server.handlers, "board_get", recorder("board_get", {"id": "board-1"}))
    monkeypatch.setattr(server.handlers, "task_get", recorder("task_get", {"id": "task-1"}))
    monkeypatch.setattr(server.handlers, "project_create", recorder("project_create", {"id": "project-2"}))
    monkeypatch.setattr(server.handlers, "project_bootstrap", recorder("project_bootstrap", {"id": "bootstrap-1"}))
    monkeypatch.setattr(server.handlers, "task_create", recorder("task_create", {"id": "task-2"}))
    monkeypatch.setattr(server.handlers, "subtask_create", recorder("subtask_create", {"id": "task-3"}))
    monkeypatch.setattr(server.handlers, "task_update", recorder("task_update", {"id": "task-2", "workflow_state": "review"}))
    monkeypatch.setattr(server.handlers, "task_claim", recorder("task_claim", {"id": "task-2"}))
    monkeypatch.setattr(server.handlers, "task_comment_add", recorder("task_comment_add", {"id": "comment-1"}))
    monkeypatch.setattr(server.handlers, "task_check_add", recorder("task_check_add", {"id": "check-1"}))
    monkeypatch.setattr(server.handlers, "task_artifact_add", recorder("task_artifact_add", {"id": "artifact-1"}))
    monkeypatch.setattr(server.handlers, "task_next", recorder("task_next", {"id": "task-next"}))
    monkeypatch.setattr(server.handlers, "task_dependencies_get", recorder("task_dependencies_get", [{"id": "dep-1"}]))
    monkeypatch.setattr(server.handlers, "task_dependency_add", recorder("task_dependency_add", {"id": "dep-1"}))
    monkeypatch.setattr(server.handlers, "task_completion_readiness", recorder("task_completion_readiness", {"can_mark_done": False}))
    monkeypatch.setattr(server.handlers, "session_spawn", recorder("session_spawn", {"id": "session-1"}))
    monkeypatch.setattr(server.handlers, "session_status", recorder("session_status", {"id": "session-1", "status": "running"}))
    monkeypatch.setattr(server.handlers, "session_follow_up", recorder("session_follow_up", {"id": "session-2"}))
    monkeypatch.setattr(server.handlers, "session_tail", recorder("session_tail", {"session_id": "session-1", "tail": ""}))
    monkeypatch.setattr(server.handlers, "session_list", recorder("session_list", [{"id": "session-1"}]))
    monkeypatch.setattr(server.handlers, "question_open", recorder("question_open", {"id": "question-1"}))
    monkeypatch.setattr(server.handlers, "question_answer_get", recorder("question_answer_get", {"id": "question-1"}))
    monkeypatch.setattr(server.handlers, "worktree_create", recorder("worktree_create", {"id": "worktree-1"}))
    monkeypatch.setattr(server.handlers, "worktree_list", recorder("worktree_list", [{"id": "worktree-1"}]))
    monkeypatch.setattr(server.handlers, "worktree_get", recorder("worktree_get", {"id": "worktree-1"}))
    monkeypatch.setattr(server.handlers, "context_search", recorder("context_search", {"hits": []}))
    monkeypatch.setattr(server.handlers, "diagnostics_get", recorder("diagnostics_get", {"health": "ok"}))
    monkeypatch.setattr(server.handlers, "worktree_hygiene_list", recorder("worktree_hygiene_list", [{"id": "worktree-1"}]))
    monkeypatch.setattr(server.handlers, "project_board_resource", recorder("project_board_resource", {"board": []}))
    monkeypatch.setattr(server.handlers, "task_detail_resource", recorder("task_detail_resource", {"task": {}}))
    monkeypatch.setattr(server.handlers, "task_completion_resource", recorder("task_completion_resource", {"can_mark_done": True}))
    monkeypatch.setattr(server.handlers, "session_timeline_resource", recorder("session_timeline_resource", {"events": []}))
    monkeypatch.setattr(server.handlers, "question_resource", recorder("question_resource", {"question": {}}))
    monkeypatch.setattr(server.handlers, "repo_inventory_resource", recorder("repo_inventory_resource", {"repos": []}))
    monkeypatch.setattr(server.handlers, "diagnostics_resource", recorder("diagnostics_resource", {"health": "ok"}))
    monkeypatch.setattr(server.handlers, "recent_events_resource", recorder("recent_events_resource", [{"id": "event-1"}]))

    assert server.project_list() == [{"id": "project-1"}]
    assert server.project_get("project-1") == {"id": "project-1"}
    assert server.board_get("project-1") == {"id": "board-1"}
    assert server.task_get("task-1") == {"id": "task-1"}
    assert server.project_create("Project", "Desc", "req-1") == {"id": "project-2"}
    assert (
        server.project_bootstrap(
            "Project",
            "/tmp/repo",
            "python-package",
            "Plan work",
            "Desc",
            False,
            "Notes",
            True,
            True,
            "req-2",
        )
        == {"id": "bootstrap-1"}
    )
    assert server.task_create("project-1", "Task", "Desc", "high", "req-3") == {"id": "task-2"}
    assert server.subtask_create("task-1", "Subtask", "Desc", "low", "req-4") == {"id": "task-3"}
    assert server.task_update("task-1", "Task", "Desc", "review", "blocked", True, "req-5") == {
        "id": "task-2",
        "workflow_state": "review",
    }
    assert server.task_claim("task-1", "agent", "session-1", "req-6") == {"id": "task-2"}
    assert server.task_comment_add("task-1", "agent", "Started", "agent", "req-7") == {"id": "comment-1"}
    assert server.task_check_add("task-1", "verification", "pending", "Need review", "req-8") == {"id": "check-1"}
    assert server.task_artifact_add("task-1", "diff", "Patch", "git:diff:HEAD", "req-9") == {"id": "artifact-1"}
    assert server.task_next("project-1") == {"id": "task-next"}
    assert server.task_dependencies_get("task-1") == [{"id": "dep-1"}]
    assert server.task_dependency_add("task-1", "task-0", "blocks", "req-10") == {"id": "dep-1"}
    assert server.task_completion_readiness("task-1") == {"can_mark_done": False}
    assert server.session_spawn("task-1", "executor", "repo-1", "worktree-1", "run", "req-11") == {"id": "session-1"}
    assert server.session_status("session-1") == {"id": "session-1", "status": "running"}
    assert server.session_follow_up("session-1", "reviewer", "review", True, True, "run", "req-12") == {
        "id": "session-2"
    }
    assert server.session_tail("session-1", 40) == {"session_id": "session-1", "tail": ""}
    assert server.session_list("project-1", "task-1") == [{"id": "session-1"}]
    assert server.question_open("task-1", "Need input?", "session-1", "blocked", "high", [{"label": "Yes"}], "req-13") == {
        "id": "question-1"
    }
    assert server.question_answer_get("question-1") == {"id": "question-1"}
    assert server.worktree_create("repo-1", "task-1", "feature", "req-14") == {"id": "worktree-1"}
    assert server.worktree_list("project-1") == [{"id": "worktree-1"}]
    assert server.worktree_get("worktree-1") == {"id": "worktree-1"}
    assert server.context_search("query", "project-1", 10) == {"hits": []}
    assert server.diagnostics_get() == {"health": "ok"}
    assert server.worktree_hygiene_list("project-1", "task-1") == [{"id": "worktree-1"}]
    assert server.project_board_state("project-1") == {"board": []}
    assert server.task_detail_state("task-1") == {"task": {}}
    assert server.task_completion_state("task-1") == {"can_mark_done": True}
    assert server.session_timeline_state("session-1") == {"events": []}
    assert server.waiting_question_state("question-1") == {"question": {}}
    assert server.repo_inventory_state("project-1") == {"repos": []}
    assert server.local_diagnostics_state() == {"health": "ok"}
    assert server.recent_project_events("project-1") == [{"id": "event-1"}]
    assert server.recent_task_events("task-1") == [{"id": "event-1"}]

    run_calls: list[str] = []
    monkeypatch.setattr(server.mcp, "run", lambda: run_calls.append("run"))
    server.main()
    assert run_calls == ["run"]

    invoked_names = {name for name, _, _ in calls}
    assert "project_bootstrap" in invoked_names
    assert "session_follow_up" in invoked_names
    assert "recent_events_resource" in invoked_names
