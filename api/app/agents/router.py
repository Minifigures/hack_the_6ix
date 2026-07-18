"""HTTP surface for multi-agent stress briefing."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.orchestrator import ALL_AGENT_IDS, run_briefing

router = APIRouter()


class BriefingRequest(BaseModel):
    building_type: str = Field(pattern="^(homestay|boutique|tower)$")
    rooms: int = Field(gt=0, le=1000)
    scenario: str = "heatwave_full"
    structure_a: str = Field(default="concrete", pattern="^(concrete|mass_timber|steel)$")
    hvac_a: str = Field(default="central_gas", pattern="^(central_gas|heat_pump)$")
    structure_b: str = Field(default="mass_timber", pattern="^(concrete|mass_timber|steel)$")
    hvac_b: str = Field(default="heat_pump", pattern="^(central_gas|heat_pump)$")
    include_agents: list[str] | None = None


@router.post("/briefing")
async def briefing(req: BriefingRequest) -> dict:
    if req.include_agents:
        unknown = [a for a in req.include_agents if a not in ALL_AGENT_IDS]
        if unknown:
            raise HTTPException(
                status_code=422,
                detail=f"unknown agents: {unknown}; known={ALL_AGENT_IDS}",
            )
    try:
        result = await run_briefing(
            building_type=req.building_type,
            rooms=req.rooms,
            scenario=req.scenario,
            structure_a=req.structure_a,
            hvac_a=req.hvac_a,
            structure_b=req.structure_b,
            hvac_b=req.hvac_b,
            include_agents=req.include_agents,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result.model_dump()
