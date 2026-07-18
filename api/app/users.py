"""Persist Auth0 signups / logins into MongoDB Atlas (InnSight.auth)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.mongo import collection

router = APIRouter(prefix="/users", tags=["users"])


class UpsertUserRequest(BaseModel):
    sub: str = Field(min_length=3, description="Auth0 user id (sub claim)")
    email: str | None = None
    name: str | None = None
    picture: str | None = None
    role: str | None = None


def _auth_collection() -> Any | None:
    return collection("auth")


def upsert_auth_user(payload: UpsertUserRequest) -> dict[str, Any]:
    coll = _auth_collection()
    if coll is None:
        return {"saved": False, "reason": "mongodb_unavailable"}

    now = datetime.now(timezone.utc)
    provider = payload.sub.split("|", 1)[0] if "|" in payload.sub else "auth0"

    update = {
        "$set": {
            "auth0_sub": payload.sub,
            "email": payload.email,
            "name": payload.name,
            "picture": payload.picture,
            "role": payload.role,
            "provider": provider,
            "last_login_at": now,
        },
        "$setOnInsert": {
            "created_at": now,
        },
    }
    result = coll.update_one({"auth0_sub": payload.sub}, update, upsert=True)
    return {
        "saved": True,
        "upserted": result.upserted_id is not None,
        "auth0_sub": payload.sub,
    }


@router.post("/upsert")
def upsert_user(req: UpsertUserRequest) -> dict[str, Any]:
    try:
        return upsert_auth_user(req)
    except Exception as exc:  # noqa: BLE001 — surface DB errors during setup
        raise HTTPException(status_code=502, detail=f"mongo upsert failed: {exc}") from exc


@router.get("/health")
def users_health() -> dict[str, Any]:
    uri_set = bool((os.environ.get("MONGODB_URI") or "").strip())
    coll = _auth_collection()
    if coll is None:
        return {"ok": False, "mongodb": False, "uri_configured": uri_set}
    try:
        count = coll.estimated_document_count()
        return {
            "ok": True,
            "mongodb": True,
            "uri_configured": uri_set,
            "auth_documents": count,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "mongodb": False,
            "uri_configured": uri_set,
            "error": str(exc),
        }
