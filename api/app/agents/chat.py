"""App-scoped chat: RAG-lite over handbook chunks + live memo context."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

PACKS_DIR = Path(__file__).resolve().parent / "packs"
HANDBOOK_PATH = PACKS_DIR / "chat_handbook.json"

_SYSTEM = """You are INN-SIGHT's in-app consultant assistant.
Only answer questions about INN-SIGHT: the map/site assembler, year stress tests,
investor memos, Option A vs B, acres/land use, climate, and honesty of the numbers.
Refuse off-topic requests briefly and steer back to the product.
Never invent kWh, $, CO2, peak kW, or recommendations — only use numbers from the
MEMO CONTEXT or say you do not have that figure (suggest Run year stress).
If the user asks to explain the memo and MEMO CONTEXT is empty, tell them to run
year stress first. Prefer short, clear answers (2–6 sentences). Cite handbook
chunk titles when you use them."""


class ChatTurn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)


class ChatSite(BaseModel):
    name: str | None = None
    lat: float | None = None
    lng: float | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)
    memo: dict[str, Any] | None = None
    briefs: dict[str, Any] | None = None
    synthesis: dict[str, Any] | None = None
    site: ChatSite | None = None


class ChatResponse(BaseModel):
    reply: str
    citations: list[str] = Field(default_factory=list)
    generator: str  # gemini | fallback
    fallback_reason: str | None = None


def _load_handbook() -> list[dict[str, Any]]:
    data = json.loads(HANDBOOK_PATH.read_text(encoding="utf-8"))
    chunks = data.get("chunks") or []
    return [c for c in chunks if isinstance(c, dict) and c.get("text")]


def retrieve_chunks(query: str, *, limit: int = 3) -> list[dict[str, Any]]:
    """Keyword score static handbook chunks (RAG-lite, no embeddings)."""
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    scored: list[tuple[int, dict[str, Any]]] = []
    for chunk in _load_handbook():
        keys = {str(k).lower() for k in (chunk.get("keywords") or [])}
        title = str(chunk.get("title") or "").lower()
        score = sum(1 for t in tokens if t in keys or t in title)
        # Soft boost when asking about memo/explain
        if {"memo", "explain", "recommend", "option"} & tokens and chunk.get("id") in {
            "memo",
            "options",
            "stress",
        }:
            score += 2
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda t: (-t[0], str(t[1].get("id"))))
    if not scored:
        # Always give product + honesty when nothing matches.
        by_id = {c.get("id"): c for c in _load_handbook()}
        return [c for c in (by_id.get("product"), by_id.get("honesty")) if c]
    return [c for _, c in scored[:limit]]


def slim_memo(memo: dict[str, Any] | None) -> dict[str, Any] | None:
    if not memo:
        return None
    options = []
    for opt in memo.get("options") or []:
        if not isinstance(opt, dict):
            continue
        options.append(
            {
                "label": opt.get("label") or opt.get("name"),
                "peak_kw": opt.get("peak_kw"),
                "strain_class": opt.get("strain_class"),
                "annual_operating_cost": opt.get("annual_operating_cost"),
                "construction_cost": opt.get("construction_cost"),
                "tco2e_total": opt.get("tco2e_total"),
                "friction": opt.get("friction"),
            }
        )
    narrative = memo.get("narrative") or {}
    comparison = memo.get("comparison") or {}
    return {
        "title": memo.get("title"),
        "scenario": memo.get("scenario"),
        "kind": memo.get("kind"),
        "recommended": comparison.get("recommended") or memo.get("recommended"),
        "options": options,
        "reasoning_chain": (memo.get("reasoning_chain") or [])[:8],
        "narrative": {
            "summary": narrative.get("summary"),
            "reasoning": (narrative.get("reasoning") or [])[:6],
            "caveats": (narrative.get("caveats") or [])[:4],
            "generator": narrative.get("generator"),
        },
        "footnote_keys": [
            f.get("key") for f in (memo.get("footnotes") or [])[:12] if isinstance(f, dict)
        ],
    }


def _build_user_prompt(
    message: str,
    history: list[ChatTurn],
    chunks: list[dict[str, Any]],
    memo: dict[str, Any] | None,
    briefs: dict[str, Any] | None,
    synthesis: dict[str, Any] | None,
    site: ChatSite | None,
) -> str:
    handbook = [
        {"id": c.get("id"), "title": c.get("title"), "text": c.get("text")}
        for c in chunks
    ]
    hist = [
        {"role": t.role, "content": t.content[:1500]}
        for t in history[-8:]
    ]
    payload = {
        "site": site.model_dump() if site else None,
        "handbook_chunks": handbook,
        "memo_context": slim_memo(memo),
        "boss_synthesis": (
            {
                "headline": (synthesis or {}).get("headline"),
                "recommendation": (synthesis or {}).get("recommendation"),
                "risks": ((synthesis or {}).get("risks") or [])[:4],
            }
            if synthesis
            else None
        ),
        "agent_brief_ids": list((briefs or {}).keys())[:8] if briefs else [],
        "recent_history": hist,
        "user_question": message,
    }
    return json.dumps(payload, default=str, indent=2)


def _fallback_reply(
    message: str,
    memo: dict[str, Any] | None,
    chunks: list[dict[str, Any]],
) -> str:
    q = message.lower()
    slim = slim_memo(memo)
    if any(w in q for w in ("memo", "explain", "recommend", "option", "why")):
        if slim and (slim.get("narrative") or {}).get("summary"):
            narr = slim["narrative"]
            parts = [str(narr.get("summary") or "").strip()]
            for line in narr.get("reasoning") or []:
                parts.append(str(line))
            rec = slim.get("recommended")
            if rec:
                parts.append(f"Recommended option: {rec}.")
            return " ".join(p for p in parts if p)[:1200]
        return (
            "No investor memo is loaded yet. Place a building, click "
            "Run year stress, then ask me to explain the memo."
        )
    if chunks:
        return str(chunks[0].get("text") or "")[:900]
    return (
        "I only help with INN-SIGHT: sites, stress tests, and memos. "
        "Ask about year stress, Option A vs B, or parcel acres."
    )


def _gemini_text(system: str, user: str, api_key: str) -> str:
    from google import genai
    from google.genai import types

    from app.agents.ai_energy import call_label, record_gemini_usage
    from app.agents.llm import GEMINI_MODEL, _GEMINI_SEM

    with _GEMINI_SEM:
        with call_label("chat"):
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=f"{system}\n\nUSER PAYLOAD:\n{user}",
                config=types.GenerateContentConfig(temperature=0.25),
            )
    record_gemini_usage(response, model=GEMINI_MODEL)
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        raise RuntimeError("empty_gemini_chat_reply")
    return text


def answer_chat(req: ChatRequest) -> ChatResponse:
    chunks = retrieve_chunks(req.message, limit=3)
    citations = [str(c.get("title") or c.get("id")) for c in chunks]
    user_prompt = _build_user_prompt(
        req.message,
        req.history,
        chunks,
        req.memo,
        req.briefs,
        req.synthesis,
        req.site,
    )

    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not key:
        return ChatResponse(
            reply=_fallback_reply(req.message, req.memo, chunks),
            citations=citations,
            generator="fallback",
            fallback_reason="no_api_key",
        )

    try:
        reply = _gemini_text(_SYSTEM, user_prompt, key)
        return ChatResponse(
            reply=reply,
            citations=citations,
            generator="gemini",
            fallback_reason=None,
        )
    except Exception as exc:
        reason = str(exc)
        if "RESOURCE_EXHAUSTED" in reason or "429" in reason:
            reason = "gemini_credits_depleted"
        else:
            reason = f"gemini_error: {reason.split('. ', 1)[0][:120]}"
        return ChatResponse(
            reply=_fallback_reply(req.message, req.memo, chunks),
            citations=citations,
            generator="fallback",
            fallback_reason=reason,
        )
