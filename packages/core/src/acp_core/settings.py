from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ACP_", extra="ignore")

    app_env: str = "development"
    app_name: str = "Agent Control Plane"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    web_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    runtime_home: Path = Field(default_factory=lambda: Path.cwd() / ".acp")
    database_name: str = "acp.sqlite3"
    bootstrap_agent_skill_path: str = "skills/agent-control-plane-api/SKILL.md"
    default_agent: str = "codex"
    kickoff_agent: str | None = None
    execution_agent: str | None = None
    review_agent: str | None = None
    verify_agent: str | None = None
    research_agent: str | None = None
    docs_agent: str | None = None
    bootstrap_agent_name: str = "codex"
    bootstrap_agent_model: str | None = None
    bootstrap_agent_permissions: str = "danger-full-access"
    bootstrap_agent_output: str | None = None
    # Deprecated compatibility bridge for legacy bootstrap command customization.
    # TODO(bootstrap-agents): remove ACP_BOOTSTRAP_AGENT_COMMAND_TEMPLATE after adapter migration.
    bootstrap_agent_command_template: str = (
        "export ACP_RUNTIME_HOME={acp_runtime_home}; "
        "codex --dangerously-bypass-approvals-and-sandbox exec - < {prompt_file}"
    )

    @property
    def data_dir(self) -> Path:
        return self.runtime_home

    @property
    def control_plane_root(self) -> Path:
        return Path(__file__).resolve().parents[4]

    @property
    def artifacts_dir(self) -> Path:
        return self.data_dir / "artifacts"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def database_path(self) -> Path:
        return self.data_dir / self.database_name

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path}"

    @property
    def api_base_url(self) -> str:
        return f"http://{self.api_host}:{self.api_port}/api/v1"

    def ensure_directories(self) -> None:
        for path in (self.data_dir, self.artifacts_dir, self.logs_dir):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
