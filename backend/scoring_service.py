# backend/scoring_service.py
from .models import ScoredAlert, Alert
from .config import PRIORITY_BUCKETS


def simple_supervised_prob(features: dict) -> float:
    # Very simple heuristic "model"
    score = 0.0
    score += 0.2 * features.get("severity_level", 1)
    score += 0.5 * features.get("ip_reputation", 0.0)
    score += 0.3 * features.get("is_login_failure", 0)
    return max(0.0, min(1.0, score))


def simple_anomaly_score(features: dict) -> float:
    hour = features.get("hour_of_day", 12)
    # Treat late-night as more anomalous
    if hour < 6 or hour > 22:
        return 0.8
    return 0.2


def compute_priority(supervised_prob: float, anomaly_score: float, rule_boost: float) -> float:
    return max(0.0, min(1.0, 0.6 * supervised_prob + 0.3 * anomaly_score + 0.1 * rule_boost))


def bucket_for_score(score: float) -> str:
    if score >= PRIORITY_BUCKETS["critical"]:
        return "CRITICAL"
    if score >= PRIORITY_BUCKETS["high"]:
        return "HIGH"
    if score >= PRIORITY_BUCKETS["medium"]:
        return "MEDIUM"
    return "LOW"


def score_alert(alert_dict: dict, features: dict) -> ScoredAlert:
    supervised_prob = simple_supervised_prob(features)
    anomaly_score = simple_anomaly_score(features)
    rule_boost = 0.0
    if "TA0006" in alert_dict.get("enrichment", {}).get("mitre_tactics", []):
        rule_boost += 0.2

    priority_score = compute_priority(supervised_prob, anomaly_score, rule_boost)
    bucket = bucket_for_score(priority_score)

    alert = Alert(**{k: alert_dict[k] for k in [
        "alert_id", "timestamp", "source", "severity", "event_type", "entities", "raw"
    ]})

    return ScoredAlert(
        **alert.dict(),
        supervised_prob=supervised_prob,
        anomaly_score=anomaly_score,
        rule_boost=rule_boost,
        priority_score=priority_score,
        priority_bucket=bucket,
        top_features=["severity_level", "ip_reputation", "is_login_failure"]
    )
