from __future__ import annotations

from typing import Any

from app.agents.llm import (
    DeterministicFallbackProvider,
    LLMProvider,
    dumps_context,
)
from app.agents.schemas import AgentBrief, BossSynthesis


def _stub_synthesis(
    comparison: dict[str, Any], briefs: dict[str, AgentBrief]
) -> BossSynthesis:
    rec = comparison.get("recommended", "A")
    a = comparison.get("option_a") or {}
    b = comparison.get("option_b") or {}
    market = briefs.get("market")
    env = briefs.get("environment")
    green = briefs.get("green_ratio")
    friction = briefs.get("friction")

    env_impact = [
        f"Sim carbon: A {a.get('tco2e_total')} vs B {b.get('tco2e_total')} tCO2e/yr; "
        f"delta {comparison.get('tco2e_delta')} tCO2e/yr favoring the lower total.",
        f"Peak strain under heat-wave stress: A {a.get('strain_class')} vs "
        f"B {b.get('strain_class')}.",
    ]
    if green:
        env_impact.append(
            f"Relative green ratio: A {green.metrics.get('a_vs_proxy')}x vs "
            f"B {green.metrics.get('b_vs_proxy')}x neighborhood proxy."
        )

    biz_impact = [
        f"Capex delta (B − A): ${comparison.get('capex_delta'):,.0f}."
        if comparison.get("capex_delta") is not None
        else "Capex delta unavailable.",
        f"Annual operating savings toward B: ${comparison.get('annual_cost_delta'):,.0f}."
        if comparison.get("annual_cost_delta") is not None
        else "Annual cost delta unavailable.",
    ]
    if market and market.metrics.get("demand_ratio") is not None:
        biz_impact.append(
            f"Stay22 demand ratio {market.metrics.get('demand_ratio')}: "
            "forward ADR supports a fully booked stress weekend narrative."
        )
    if friction:
        biz_impact.append(
            f"Community friction A {friction.metrics.get('score_a')} vs "
            f"B {friction.metrics.get('score_b')} (heuristic)."
        )

    abatement = comparison.get("abatement_cost")
    threshold = comparison.get("abatement_threshold")
    alignment = (
        f"Deterministic engine recommends Option {rec}. "
        f"Abatement ${abatement}/tCO2e vs ${threshold}/t threshold."
        if abatement is not None
        else f"Deterministic engine recommends Option {rec}."
    )

    open_q = [
        "Confirm TGS / site-plan pathway for this parcel.",
        "Validate Stay22 ADR against an operator revenue model.",
    ]
    if env and any(s.status != "live" for s in env.sources if s.label.startswith("Electricity")):
        open_q.append("Wire live Electricity Maps intensity for peak-hour carbon.")

    summary = (
        f"Boss synthesis: engine pick is Option {rec}. Environmental case "
        f"hinges on tCO2e and peak strain; business case on capex premium vs "
        f"operating savings and market demand pressure."
    )

    return BossSynthesis(
        environmental_impact=env_impact[:4],
        business_impact=biz_impact[:4],
        recommendation_alignment=alignment,
        reinforces_sim=True,
        open_questions=open_q[:4],
        summary=summary,
    )


def synthesize_boss(
    provider: LLMProvider,
    comparison: dict[str, Any],
    briefs: dict[str, AgentBrief],
) -> BossSynthesis:
    stub = _stub_synthesis(comparison, briefs)
    if isinstance(provider, DeterministicFallbackProvider):
        return stub

    try:
        system = (
            "You are the lead analyst (Boss) for INN-SIGHT. Synthesize specialist "
            "briefs with the deterministic sim comparison. Do not invent numbers. "
            "Canadian spelling. No em dashes. State whether specialist context "
            "reinforces or challenges the sim recommendation."
        )
        payload = {
            "comparison": comparison,
            "briefs": {k: v.model_dump() for k, v in briefs.items()},
        }
        user = (
            "Return BossSynthesis JSON: environmental_impact, business_impact, "
            "recommendation_alignment, reinforces_sim, open_questions, summary.\n\n"
            + dumps_context(payload)
        )
        result = provider.complete_json(system, user, BossSynthesis)
        return BossSynthesis.model_validate(result.model_dump())
    except Exception:
        return stub
