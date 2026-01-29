# backend/enricher.py
from .models import Alert


def fake_ip_reputation(ip: str) -> float:
    if not ip:
        return 0.0
    # toy logic: treat private ranges as low risk
    if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172.16."):
        return 0.1
    return 0.8


def enrich_alert(alert: Alert) -> dict:
    ip = alert.entities.get("ip")
    reputation = fake_ip_reputation(ip)

    enriched = alert.dict()
    enriched["enrichment"] = {
        "ip_reputation": reputation,
        "mitre_tactics": ["TA0006"] if alert.event_type == "login_failure" else []
    }
    return enriched
