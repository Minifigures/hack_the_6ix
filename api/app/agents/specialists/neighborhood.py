from __future__ import annotations

from typing import Any

from app.agents.llm import LLMProvider
from app.agents.schemas import AgentBrief
from app.agents.specialists import run_specialist, src


def analyze_neighborhood(provider: LLMProvider, ctx: dict[str, Any]) -> AgentBrief:
    nb = ctx.get("neighborhood") or {}
    market = ctx.get("market") or {}
    target = market.get("target") or {}

    findings = [
        f"{nb.get('site_name')} sits in {nb.get('neighbourhood')}: {nb.get('land_use')}",
        f"Transit: {nb.get('transit')}",
        f"Walkability: {nb.get('walkability')}",
    ]
    if target.get("properties"):
        findings.append(
            f"Stay22 sample shows {target['properties']} accommodations within 3 km "
            f"— dense local competition for short stays."
        )

    constraints = nb.get("constraints") or []
    risks = list(constraints[:3]) if constraints else [
        "Neighborhood pack is an estimate, not a planning study."
    ]

    stub = AgentBrief(
        agent_id="neighborhood",
        title="Neighborhood",
        findings=findings[:4],
        metrics={
            "lat": nb.get("lat"),
            "lng": nb.get("lng"),
            "nearby_listings": target.get("properties"),
            "site_name": nb.get("site_name"),
        },
        risks=risks,
        sources=[
            src("Neighborhood site pack", "estimate"),
            src("Stay22 listing density (counts only)", market.get("source") or "estimate"),
        ],
        confidence=0.55,
    )
    return run_specialist(
        provider,
        agent_id="neighborhood",
        title="Neighborhood",
        focus="Local land use, transit, competition density, and guest-demand context.",
        context={"neighborhood": nb, "market": market},
        stub=stub,
    )
