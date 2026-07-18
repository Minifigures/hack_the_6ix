from __future__ import annotations

from typing import Any

from app.agents.llm import LLMProvider
from app.agents.schemas import AgentBrief
from app.agents.specialists import run_specialist, src


def analyze_compliance(provider: LLMProvider, ctx: dict[str, Any]) -> AgentBrief:
    pack = ctx.get("compliance") or {}
    cmp_ = ctx.get("comparison") or {}
    a = cmp_.get("option_a") or {}
    bt = a.get("building_type") or "boutique"
    type_notes = (pack.get("building_type_notes") or {}).get(bt, "")

    energy = pack.get("energy_and_climate") or []
    findings = [
        f"Jurisdiction: {pack.get('jurisdiction')}.",
        f"Building-type note ({bt}): {type_notes}" if type_notes else f"Type: {bt}.",
    ]
    for item in energy[:2]:
        findings.append(f"{item.get('item')}: {item.get('note')}")

    structure_a = a.get("structure")
    structure_b = (cmp_.get("option_b") or {}).get("structure")
    if structure_b == "mass_timber" or structure_a == "mass_timber":
        findings.append(
            "Mass timber: EMTC allowed under recent OBC amendments within "
            "height/area limits; fire/acoustic detailing adds design cost."
        )

    risks = [
        "Compliance pack is an estimate/heuristic checklist, not legal advice.",
        "Site plan / TGS applicability depends on actual planning pathway.",
    ]

    stub = AgentBrief(
        agent_id="compliance",
        title="Government / compliance",
        findings=findings[:4],
        metrics={
            "jurisdiction": pack.get("jurisdiction"),
            "building_type": bt,
            "structure_a": structure_a,
            "structure_b": structure_b,
            "hvac_a": a.get("hvac"),
            "hvac_b": (cmp_.get("option_b") or {}).get("hvac"),
        },
        risks=risks,
        sources=[
            src("Ontario/Toronto hospitality + energy checklist", "estimate"),
        ],
        confidence=0.45,
    )
    return run_specialist(
        provider,
        agent_id="compliance",
        title="Government / compliance",
        focus="Permits, energy/TGS exposure, mass-timber vs concrete compliance notes.",
        context={"compliance": pack, "comparison": cmp_},
        stub=stub,
    )
