from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from acp_core.errors import AcpServiceError
from acp_core.schemas import ApiErrorEnvelope

RUNTIME_ERROR_RESPONSES = {
    502: {"model": ApiErrorEnvelope, "description": "Runtime adapter failure."},
    503: {"model": ApiErrorEnvelope, "description": "Runtime subsystem unavailable."},
    504: {"model": ApiErrorEnvelope, "description": "Runtime adapter timeout."},
}


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AcpServiceError)
    async def handle_acp_service_error(_request: Request, exc: AcpServiceError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_response())
