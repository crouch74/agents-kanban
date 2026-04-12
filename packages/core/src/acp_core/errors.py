from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AcpServiceError(Exception):
    message: str
    code: str
    status_code: int
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool | None = None

    def __str__(self) -> str:
        return self.message

    def to_response(self) -> dict[str, Any]:
        error: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            error["details"] = self.details
        if self.retryable is not None:
            error["retryable"] = self.retryable
        return {"error": error}


class RuntimeServiceError(AcpServiceError):
    pass


def build_runtime_service_error(
    *,
    operation: str,
    exc: Exception,
    details: dict[str, Any] | None = None,
) -> RuntimeServiceError:
    status_code = 502
    code = "runtime_adapter_failure"
    message = f"Runtime adapter failed during {operation.replace('_', ' ')}."

    if isinstance(exc, TimeoutError):
        status_code = 504
        code = "runtime_timeout"
        message = f"Timed out during {operation.replace('_', ' ')}."
    elif isinstance(exc, ConnectionError):
        status_code = 503
        code = "runtime_unavailable"
        message = "Runtime adapter is temporarily unavailable."

    error_details = {
        "adapter": "tmux",
        "operation": operation,
    }
    if details:
        error_details.update(details)

    return RuntimeServiceError(
        message=message,
        code=code,
        status_code=status_code,
        details=error_details,
        retryable=status_code in {502, 503, 504},
    )
