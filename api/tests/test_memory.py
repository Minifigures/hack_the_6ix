"""Backboard memory layer: strictly additive, silent without a key."""

import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))


def test_disabled_without_key(monkeypatch) -> None:
    monkeypatch.delenv("BACKBOARD_API_KEY", raising=False)
    from app.agents import memory

    assert memory.enabled() is False
    assert memory.recall("auth0|u1", "investor", "payback?") == []
    memory.remember("auth0|u1", "investor", "q", "a")  # must not raise


def test_chat_without_memory_unchanged(monkeypatch) -> None:
    monkeypatch.delenv("BACKBOARD_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from app.agents.chat import ChatRequest, answer_chat

    res = answer_chat(ChatRequest(message="what is a memo"))
    assert res.reply
    assert res.memories_used == 0


def test_backboard_fallback_none_without_key(monkeypatch) -> None:
    monkeypatch.delenv("BACKBOARD_API_KEY", raising=False)
    from app.agents import memory

    assert memory.generate_fallback("auth0|u1", "investor", "hello") is None


class _Res:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


def _wire(monkeypatch, payload: dict):
    """Enable the key, pin the assistant id, and stub the HTTP reply."""
    from app.agents import memory

    monkeypatch.setenv("BACKBOARD_API_KEY", "espr_test")
    monkeypatch.setattr(memory, "_ensure_assistant", lambda sub, role: "asst_1")
    sent: dict = {}

    def fake_post(url, *, headers=None, json=None, files=None, timeout=None):
        sent["url"] = url
        sent["json"] = json
        return _Res(payload)

    monkeypatch.setattr(memory.httpx, "post", fake_post)
    return memory, sent


def test_backboard_fallback_reads_content_not_message(monkeypatch) -> None:
    # Backboard's "message" field is a status string; the reply is "content".
    memory, sent = _wire(
        monkeypatch,
        {
            "message": "Message sent successfully",
            "content": "Timber pencils out at $159/t.",
            "retrieved_memories": [{"content": "worried about payback"}],
        },
    )
    out = memory.generate_fallback("auth0|u1", "investor", "does timber pay?")
    assert out == ("Timber pencils out at $159/t.", 1)
    assert sent["json"]["memory"] == "Auto"
    assert sent["json"]["assistant_id"] == "asst_1"


def test_backboard_fallback_none_on_status_only_reply(monkeypatch) -> None:
    memory, _ = _wire(
        monkeypatch, {"message": "Message sent successfully", "content": ""}
    )
    assert memory.generate_fallback("auth0|u1", "investor", "hi") is None


def test_recall_returns_memory_contents(monkeypatch) -> None:
    memory, sent = _wire(
        monkeypatch,
        {
            "memories": [
                {"content": "asked about payback period"},
                {"content": ""},
                {"content": "prefers Option B"},
            ]
        },
    )
    out = memory.recall("auth0|u1", "investor", "payback")
    assert out == ["asked about payback period", "prefers Option B"]
    assert sent["url"].endswith("/assistants/asst_1/memories/search")


def test_remember_posts_exchange_silently(monkeypatch) -> None:
    memory, sent = _wire(monkeypatch, {"message": "ok"})
    memory.remember("auth0|u1", "investor", "why B?", "lower abatement cost")
    assert sent["url"].endswith("/assistants/asst_1/memories")
    assert sent["json"]["content"].startswith("Q: why B?")
    assert sent["json"]["metadata"]["app"] == "innsight"
