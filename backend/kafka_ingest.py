# backend/kafka_ingest.py
import json
from kafka import KafkaConsumer
from .config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_ALERT_TOPIC
from .normalizer import normalize_alert
from .enricher import enrich_alert
from .feature_engine import build_features
from .scoring_service import score_alert
from .correlation_service import add_scored_alert


def run_kafka_ingest():
    consumer = KafkaConsumer(
        KAFKA_ALERT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    for msg in consumer:
        raw_alert = msg.value
        norm = normalize_alert(raw_alert)
        enriched = enrich_alert(norm)
        features = build_features(enriched)
        scored = score_alert(enriched, features)
        add_scored_alert(scored)
