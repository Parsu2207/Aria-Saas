# backend/correlation_service.py
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List
from .models import ScoredAlert, Incident

# In-memory store for demo desktop app
_scored_alerts: List[ScoredAlert] = []
_incidents: List[Incident] = []


def add_scored_alert(alert: ScoredAlert):
    _scored_alerts.append(alert)
    _rebuild_incidents()


def _rebuild_incidents(window_minutes: int = 15):
    global _incidents

    # For demo: ignore time window and use all alerts
    recent = list(_scored_alerts)
    grouped = defaultdict(list)

    for a in recent:
        key = a.entities.get("user") or a.entities.get("ip") or "unknown"
        grouped[key].append(a)

    now = datetime.utcnow()
    incidents = []
    for idx, (entity, alerts) in enumerate(grouped.items(), start=1):
        bucket = max(alerts, key=lambda x: x.priority_score).priority_bucket
        incidents.append(
            Incident(
                incident_id=f"INC-{idx}",
                alerts=alerts,
                created_at=now,
                entities={"entity": entity},
                priority_bucket=bucket,
            )
        )

    _incidents = incidents


def list_incidents() -> List[Incident]:
    return _incidents


def list_alerts() -> List[ScoredAlert]:
    return sorted(_scored_alerts, key=lambda a: a.priority_score, reverse=True)
