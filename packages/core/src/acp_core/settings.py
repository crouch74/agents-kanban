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
    web_origin: str = "http://127.0.0.1:5173"
    runtime_home: Path = Field(default_factory=lambda: Path.cwd() / ".acp")
    database_name: str = "acp.sqlite3"

    @property
    def data_dir(self) -> Path:
        return self.runtime_home

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

    def ensure_directories(self) -> None:
        for path in (self.data_dir, self.artifacts_dir, self.logs_dir):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()

