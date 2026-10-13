"""
FastAPI REST API Server for Gi Bleed Urgent Triage Agent.
"""
from typing import Dict, Any, List
import os
import hmac
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Gi Bleed Urgent Triage Agent API",
    description="Legacy generic demonstration only; not a validated clinical decision support API.",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "DEMO_ONLY", "service": "gi-bleed-urgent-triage-agent", "note": "Not validated for clinical use"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    if os.getenv("ENABLE_DEMO_AUDIT_API") != "1":
        raise HTTPException(status_code=503, detail="Generic demo audit is disabled; use /api/gbs on the clinical API.")
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs(authorization: str = Header(default="")):
    token = os.getenv("AUDIT_LOG_READ_TOKEN")
    if not token:
        raise HTTPException(status_code=404, detail="Audit log endpoint unavailable")
    expected = "Bearer " + token
    if not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
