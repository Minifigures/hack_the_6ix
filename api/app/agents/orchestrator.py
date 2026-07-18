"""Orchestrate gather -> specialists (parallel) -> boss."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from typing import Any, Callable

from innsight_model.sim import BuildingConfig, Comparison, SCENARIOS, compare

from app.agents.gather import gather_all
from app.agents.llm import LLMProvider, get_provider
from app.agents.schemas import AgentBrief, BossSynthesis, BriefingResponse
from app.agents.specialists.boss import synthesize_boss
from app.agents.specialists.compliance import analyze_compliance
from app.agents.specialists.environment import analyze_environment
from app.agents.specialists.friction import analyze_friction
from app.agents.specialists.green_ratio import analyze_green_ratio
from app.agents.specialists.market import analyze_market
from app.agents.specialists.neighborhood import analyze_neighborhood

SPECIALISTS: dict[str, Callable[[LLMProvider, dict[str, Any]], AgentBrief]] = {
    "market": analyze_market,
    "environment": analyze_environment,
    "neighborhood": analyze_neighborhood,
    "green_ratio": analyze_green_ratio,
    "friction": analyze_friction,
    "compliance": analyze_compliance,
}

ALL_AGENT_IDS = list(SPECIALISTS.keys())


def _serialize_comparison(comparison: Comparison) -> dict[str, Any]:
    payload = asdict(comparison)
    payload["option_a"]["config"] = asdict(comparison.option_a.config)
    payload["option_b"]["config"] = asdict(comparison.option_b.config)
    return payload


def _run_specialists(
    provider: LLMProvider,
    ctx: dict[str, Any],
    include: list[str],
) -> dict[str, AgentBrief]:
    selected = [aid for aid in include if aid in SPECIALISTS]

    def _one(agent_id: str) -> tuple[str, AgentBrief]:
        return agent_id, SPECIALISTS[agent_id](provider, ctx)

    briefs: dict[str, AgentBrief] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(selected))) as pool:
        for agent_id, brief in pool.map(_one, selected):
            briefs[agent_id] = brief
    return briefs


async def run_briefing(
    *,
    building_type: str,
    rooms: int,
    scenario: str = "heatwave_full",
    structure_a: str = "concrete",
    hvac_a: str = "central_gas",
    structure_b: str = "mass_timber",
    hvac_b: str = "heat_pump",
    include_agents: list[str] | None = None,
    provider: LLMProvider | None = None,
) -> BriefingResponse:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario}")

    config_a = BuildingConfig(
        building_type,
        rooms,
        structure_a,
        hvac_a,
        "Option A: Concrete + Central HVAC"
        if structure_a == "concrete" and hvac_a == "central_gas"
        else f"Option A: {structure_a} + {hvac_a}",
    )
    config_b = BuildingConfig(
        building_type,
        rooms,
        structure_b,
        hvac_b,
        "Option B: Mass Timber + Heat Pumps"
        if structure_b == "mass_timber" and hvac_b == "heat_pump"
        else f"Option B: {structure_b} + {hvac_b}",
    )
    comparison = compare(config_a, config_b, SCENARIOS[scenario])
    ctx = await gather_all(comparison)

    llm, fallback_reason = (provider, None) if provider is not None else get_provider()
    include = include_agents or ALL_AGENT_IDS
    briefs = _run_specialists(llm, ctx, include)
    synthesis: BossSynthesis = synthesize_boss(
        llm, ctx["comparison"], briefs
    )

    return BriefingResponse(
        comparison=_serialize_comparison(comparison),
        briefs=briefs,
        synthesis=synthesis,
        generator=llm.name,
        fallback_reason=fallback_reason,
    )
