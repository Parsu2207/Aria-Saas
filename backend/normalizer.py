# backend/normalizer.py
from datetime import datetime
from .models import Alert

def _parse_timestamp(ts):
    if not isinstance(ts, str):
        return datetime.utcnow()
    # strip trailing Z if present
    if ts.endswith("Z"):
        ts = ts[:-1]
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.utcnow()

def normalize_alert(raw: dict) -> Alert:
    alert_id = raw.get("id") or raw.get("_id") or "unknown"
    ts = raw.get("timestamp") or raw.get("@timestamp")
    timestamp = _parse_timestamp(ts)

    return Alert(
        alert_id=str(alert_id),
        timestamp=timestamp,
        source=raw.get("source", "splunk"),
        severity=raw.get("severity", "medium"),
        event_type=raw.get("event_type", raw.get("sourcetype", "unknown")),
        entities={
            "ip": raw.get("src_ip") or raw.get("ip") or "unknown",
            "user": raw.get("user") or raw.get("username") or "unknown",
        },
        raw=raw,
    )
