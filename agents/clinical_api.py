"""Stateless clinical-score HTTP API. No patient identifiers are accepted."""
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

from gibleed_sentinel import calculate_aims65, calculate_gbs, calculate_rockall

app = FastAPI(
    title="Upper GI bleeding risk score calculators",
    description="Educational clinical decision support; not a disposition or treatment service.",
    version="2.1.0",
    docs_url="/docs",
)


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GBSRequest(StrictInput):
    bun_mmol_l: float = Field(ge=0, le=100, allow_inf_nan=False)
    hemoglobin_g_dl: float = Field(ge=0, le=25, allow_inf_nan=False)
    sex: Literal["male", "female"]
    sbp_mmhg: float = Field(ge=0, le=300, allow_inf_nan=False)
    heart_rate: float = Field(ge=0, le=300, allow_inf_nan=False)
    melena: bool
    syncope: bool
    hepatic_disease: bool
    cardiac_failure: bool


class AIMS65Request(StrictInput):
    albumin_g_dl: float = Field(ge=0, le=10, allow_inf_nan=False)
    inr: float = Field(ge=0, le=20, allow_inf_nan=False)
    mental_status_altered: bool
    sbp_mmhg: float = Field(ge=0, le=300, allow_inf_nan=False)
    age: int = Field(ge=0, le=150)


class RockallRequest(StrictInput):
    age: int = Field(ge=0, le=150)
    shock_hr: float = Field(ge=0, le=300, allow_inf_nan=False)
    shock_sbp: float = Field(ge=0, le=300, allow_inf_nan=False)
    comorbidity: Literal["none", "cardiac", "major"]
    endoscopic_diagnosis: Literal["none", "peptic_ulcer", "cancer"]
    major_stigmata: Literal["none", "blood", "visible_vessel", "active_bleeding"]


@app.middleware("http")
async def disable_caching(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "gi-bleed-urgent-triage-agent"}


@app.post("/api/gbs")
def gbs(req: GBSRequest):
    return calculate_gbs(**req.model_dump())


@app.post("/api/aims65")
def aims65(req: AIMS65Request):
    return calculate_aims65(**req.model_dump())


@app.post("/api/rockall")
def rockall(req: RockallRequest):
    return calculate_rockall(**req.model_dump())
