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
