"""Backboard.io per-stakeholder memory for the consultant chat.

One Backboard assistant per (Auth0 sub, role); the mapping lives in Mongo
(process dict fallback) because Backboard has no external-id lookup. The
memory layer is strictly additive: no key, network trouble, or missing user
means the chat behaves exactly as before. Endpoints verified against the
Backboard docs (X-API-Key auth, assistants/memories/search).
"""

from __future__ import annotations

import os
from typing import Any

import httpx

BASE_URL = "https://app.backboard.io/api"
_TIMEOUT = 4.0

_map_fallback: dict[str, str] = {}


def enabled() -> bool:
    return bool((os.environ.get("BACKBOARD_API_KEY") or "").strip())


def _headers() -> dict[str, str]:
    return {
        "X-API-Key": (os.environ.get("BACKBOARD_API_KEY") or "").strip(),
        "Content-Type": "application/json",
    }


def _map_key(sub: str, role: str) -> str:
    return f"{sub}|{role or 'stakeholder'}"


def _load_mapping(key: str) -> str | None:
    try:
        from app.mongo import collection

        coll = collection("backboard_map")
        if coll is not None:
            doc = coll.find_one({"key": key})
            if doc and doc.get("assistant_id"):
                return str(doc["assistant_id"])
    except Exception:
        pass
    return _map_fallback.get(key)

def _store_mapping(key: str, assistant_id: str) -> None:
    _map_fallback[key] = assistant_id
    try:
        from app.mongo import collection

        coll = collection("backboard_map")
        if coll is not None:
            coll.update_one(
                {"key": key},
                {"$set": {"assistant_id": assistant_id}},
                upsert=True,
            )
    except Exception:
        pass


def _ensure_assistant(sub: str, role: str) -> str | None:
    key = _map_key(sub, role)
    existing = _load_mapping(key)
    if existing:
        return existing
    try:
        res = httpx.post(
            f"{BASE_URL}/assistants",
            headers=_headers(),
            json={
                "name": f"innsight-{role or 'stakeholder'}-{sub[-10:]}",
                "system_prompt": (
                    "Memory space for one INN-SIGHT stakeholder "
                    f"({role or 'stakeholder'}). Stores their questions, "
                    "concerns, and decisions across sessions."
                ),
            },
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        assistant_id = str((res.json() or {}).get("assistant_id") or "")
        if assistant_id:
            _store_mapping(key, assistant_id)
            return assistant_id
    except Exception:
        pass
    return None


def recall(sub: str, role: str, query: str, limit: int = 4) -> list[str]:
    """Top matching memories for this stakeholder, empty on any trouble."""
    if not enabled() or not sub:
        return []
    assistant_id = _ensure_assistant(sub, role)
    if not assistant_id:
        return []
    try:
        res = httpx.post(
            f"{BASE_URL}/assistants/{assistant_id}/memories/search",
            headers=_headers(),
            json={"query": query[:500], "limit": limit},
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        memories = (res.json() or {}).get("memories") or []
        return [
            str(m.get("content"))[:400]
            for m in memories
            if m.get("content")
        ][:limit]
    except Exception:
        return []


def remember(sub: str, role: str, question: str, reply: str) -> None:
    """Store the exchange; failures are silent by design."""
    if not enabled() or not sub:
        return
    assistant_id = _ensure_assistant(sub, role)
    if not assistant_id:
        return
    try:
        httpx.post(
            f"{BASE_URL}/assistants/{assistant_id}/memories",
            headers=_headers(),
            json={
                "content": f"Q: {question[:400]}\nA: {reply[:600]}",
                "metadata": {"role": role or "stakeholder", "app": "innsight"},
            },
            timeout=_TIMEOUT,
        )
    except Exception:
        pass
