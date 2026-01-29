# backend/api_server.py
from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from typing import List
import json
from .models import ScoredAlert, Incident
from .correlation_service import list_alerts, list_incidents
from .playbook_engine import execute_playbook
from .correlation_service import add_scored_alert
from .normalizer import normalize_alert
from .enricher import enrich_alert
from .feature_engine import build_features
from .scoring_service import score_alert


app = FastAPI(title="ARIA Desktop Backend API")
@app.post("/api/v1/debug/upload_json")
async def debug_upload_json(file: UploadFile = File(...)):
    # 1) Read and parse file
    if file.content_type not in ("application/json", "text/json"):
        raise HTTPException(status_code=400, detail="File must be JSON")

    raw_bytes = await file.read()
    try:
        alerts = json.loads(raw_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON structure")

    if not isinstance(alerts, list):
        raise HTTPException(status_code=400, detail="JSON must be a list of alerts")

    # 2) Ingest + score alerts (same as ingest_raw)
    injected_ids = []
    for raw in alerts:
        norm = normalize_alert(raw)
        enriched = enrich_alert(norm)
        feats = build_features(enriched)
        scored = score_alert(enriched, feats)
        add_scored_alert(scored)
        injected_ids.append(scored.alert_id)

    # 3) Auto-select top incident and run playbook
    incidents = list_incidents()
    playbook_result = None
    if incidents:
        bucket_order = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
        top_incident = sorted(
            incidents,
            key=lambda i: (
                bucket_order.get(i.priority_bucket, 0),
                max(a.priority_score for a in i.alerts),
            ),
            reverse=True,
        )[0]
        playbook_result = execute_playbook(top_incident, "create_ticket")

    return {
        "inserted": injected_ids,
        "count": len(injected_ids),
        "auto_playbook": playbook_result,
    }
"""    
@app.post("/api/v1/debug/ingest_raw")
def debug_ingest_raw(alerts: List[dict] = Body(...)):
    #Debug-only: ingest raw alerts, normalize + score + store.
    injected_ids = []
    for raw in alerts:
        norm = normalize_alert(raw)
        enriched = enrich_alert(norm)
        feats = build_features(enriched)
        scored = score_alert(enriched, feats)
        add_scored_alert(scored)
        injected_ids.append(scored.alert_id)
    return {"inserted": injected_ids, "count": len(injected_ids)}
"""
@app.get("/api/v1/alerts", response_model=List[ScoredAlert])
def get_alerts(priority: str | None = None):
    alerts = list_alerts()
    if priority:
        priority = priority.upper()
        alerts = [a for a in alerts if a.priority_bucket == priority]
    return alerts

@app.get("/api/v1/incidents", response_model=List[Incident])
def get_incidents():
    return list_incidents()

@app.post("/api/v1/playbooks/{playbook_id}")
def run_playbook(playbook_id: str, incident_id: str):
    incidents = list_incidents()
    match = next((i for i in incidents if i.incident_id == incident_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Incident not found")
    return execute_playbook(match, playbook_id)
