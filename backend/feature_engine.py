# backend/feature_engine.py
from datetime import datetime


def build_features(enriched_alert: dict) -> dict:
    # Minimal placeholder; you can query DB for history later
    now = datetime.utcnow()
    base = enriched_alert

    features = {
        "severity_level": {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(
            base.get("severity", "medium").lower(), 1
        ),
        "ip_reputation": base.get("enrichment", {}).get("ip_reputation", 0.0),
        "is_login_failure": 1 if base.get("event_type") == "login_failure" else 0,
        "hour_of_day": now.hour,
    }
    return features
