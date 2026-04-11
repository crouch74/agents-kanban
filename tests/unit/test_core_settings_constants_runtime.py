from __future__ import annotations

import importlib
import sys
import types


def test_settings_computed_paths_and_urls(tmp_path):
    from acp_core.settings import Settings

    settings = Settings(runtime_home=tmp_path, api_host="0.0.0.0", api_port=9000, database_name="test.sqlite3")

    assert settings.data_dir == tmp_path
    assert settings.artifacts_dir == tmp_path / "artifacts"
    assert settings.logs_dir == tmp_path / "logs"
    assert settings.database_path == tmp_path / "test.sqlite3"
    assert settings.database_url == f"sqlite:///{tmp_path / 'test.sqlite3'}"
    assert settings.api_base_url == "http://0.0.0.0:9000/api/v1"


def test_settings_ensure_directories_creates_runtime_tree(tmp_path):
    from acp_core.settings import Settings

    settings = Settings(runtime_home=tmp_path / "runtime")
    settings.ensure_directories()

    assert settings.data_dir.exists()
    assert settings.artifacts_dir.exists()
    assert settings.logs_dir.exists()


def test_constants_cover_default_columns_and_transitions():
    from acp_core.constants import DEFAULT_BOARD_COLUMNS, TASK_TRANSITIONS, WORKFLOW_BY_COLUMN_KEY

    column_keys = [column["key"] for column in DEFAULT_BOARD_COLUMNS]
    assert column_keys == ["backlog", "ready", "in_progress", "review", "done"]
    assert set(WORKFLOW_BY_COLUMN_KEY.keys()) == set(column_keys)
    assert TASK_TRANSITIONS["review"] == {"in_progress", "done", "cancelled"}


def test_runtime_helper_functions_without_real_tmux(monkeypatch):
    fake_libtmux = types.ModuleType("libtmux")

    class FakeServer:  # pragma: no cover - behavior unused by helper tests
        pass

    fake_libtmux.Server = FakeServer
    monkeypatch.setitem(sys.modules, "libtmux", fake_libtmux)

    runtime_module = importlib.import_module("acp_core.runtime")
    runtime_module = importlib.reload(runtime_module)

    assert runtime_module.safe_tmux_name("My Session / Branch!") == "my-session---branch"
    assert runtime_module.safe_tmux_name("***") == "acp-session"
    assert runtime_module.shell_join(["echo", "hello world", "$(rm -rf /)"]) == "echo 'hello world' '$(rm -rf /)'"
    assert isinstance(runtime_module.DEFAULT_PROFILE_COMMANDS, dict)
