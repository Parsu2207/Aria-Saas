# backend/models.py
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime


class Alert(BaseModel):
    alert_id: str
    timestamp: datetime
    source: str
    severity: str
    event_type: str
    entities: Dict[str, str]
    raw: Dict


class ScoredAlert(Alert):
    supervised_prob: float
    anomaly_score: float
    rule_boost: float
    priority_score: float
    priority_bucket: str
    top_features: List[str]


class Incident(BaseModel):
    incident_id: str
    alerts: List[ScoredAlert]
    created_at: datetime
    entities: Dict[str, str]
    priority_bucket: str
