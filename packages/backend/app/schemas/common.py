"""Shared schema bases and the MCP response envelope (PRD §6.2)."""
from __future__ import annotations

import datetime as dt
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base for read schemas mapped straight from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class MCPMeta(BaseModel):
    user_id: str
    fetched_at: dt.datetime
    context_note: str | None = None


class MCPSuccess(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: MCPMeta


class MCPError(BaseModel):
    success: bool = False
    error: str
    # NOT_FOUND | UNAUTHORIZED | INVALID_PARAMS | VALIDATION_FAILED
    code: str


def mcp_ok(data: Any, *, user_id: str, context_note: str | None = None) -> dict:
    return {
        "success": True,
        "data": data,
        "meta": {
            "user_id": user_id,
            "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "context_note": context_note,
        },
    }


def mcp_err(error: str, code: str = "INVALID_PARAMS") -> dict:
    return {"success": False, "error": error, "code": code}
