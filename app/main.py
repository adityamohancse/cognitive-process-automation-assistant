from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from ibm_cloud_sdk_core.api_exception import ApiException
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .watson_client import WatsonAssistantClient

load_dotenv()

app = FastAPI(
    title="IT Support Automation Assistant API",
    version="1.0.0",
    description="Learning/demo API for a watsonx Assistant custom extension and runtime client.",
)

TICKET_TYPES = {"password_reset", "laptop_request", "access_request"}
TICKETS: dict[str, dict[str, Any]] = {}


class TicketRequest(BaseModel):
    ticket_type: Literal["password_reset", "laptop_request", "access_request"]
    employee_id: str = Field(min_length=3, max_length=32)
    department: str | None = Field(default=None, max_length=100)
    laptop_type: str | None = Field(default=None, max_length=100)
    justification: str | None = Field(default=None, max_length=1000)
    system_name: str | None = Field(default=None, max_length=200)
    manager_name: str | None = Field(default=None, max_length=200)
    identity_verified: bool = False
    approval_required: bool = False
    route_to: str | None = Field(default=None, max_length=200)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


def validate_employee_id(employee_id: str) -> None:
    if not re.fullmatch(r"[Ee]\d{5,8}", employee_id.strip()):
        raise HTTPException(
            status_code=422,
            detail="employee_id must look like E12345",
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/create-ticket")
def create_ticket(request: TicketRequest) -> dict[str, Any]:
    """Create a mock ticket; replace this with an ITSM adapter in production."""
    validate_employee_id(request.employee_id)

    if request.ticket_type == "password_reset" and not request.identity_verified:
        raise HTTPException(
            status_code=400,
            detail="identity_verified must be true for password reset tickets",
        )
    if request.ticket_type == "laptop_request":
        missing = [
            field
            for field in ("department", "laptop_type", "justification")
            if not getattr(request, field)
        ]
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"Missing laptop request fields: {', '.join(missing)}",
            )
    if request.ticket_type == "access_request":
        missing = [
            field
            for field in ("system_name", "manager_name")
            if not getattr(request, field)
        ]
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"Missing access request fields: {', '.join(missing)}",
            )

    ticket_id = f"IT-{uuid.uuid4().hex[:8].upper()}"
    status = "PENDING_APPROVAL" if request.approval_required else "OPEN"
    ticket = {
        "ticket_id": ticket_id,
        "status": status,
        "ticket_type": request.ticket_type,
        "employee_id": request.employee_id.upper(),
        "route_to": request.route_to or "IT service desk",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "details": request.model_dump(exclude_none=True),
        "next_step": (
            "An approver reviews the request"
            if request.approval_required
            else "The service desk reviews the request"
        ),
    }
    TICKETS[ticket_id] = ticket
    return ticket


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    """Send a message to Assistant v2 when the account entitlement is enabled."""
    try:
        client = WatsonAssistantClient.from_environment()
        session_id = request.session_id or client.create_session()
        result = client.send_message(session_id, request.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ApiException as exc:
        raise HTTPException(
            status_code=502,
            detail="Watson Assistant request failed; inspect server logs for the SDK error.",
        ) from exc

    return {
        "session_id": session_id,
        "messages": client.text_from_response(result),
        "raw": result,
    }
