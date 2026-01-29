# backend/config.py
KAFKA_BOOTSTRAP_SERVERS = ["localhost:9092"]
KAFKA_ALERT_TOPIC = "aria_alerts"

POSTGRES_DSN = "postgresql://aria:aria@localhost:5432/aria"
ELASTICSEARCH_URL = "http://localhost:9200"

SCORING_SERVICE_URL = "http://127.0.0.1:8000/docs"
API_BIND_HOST = "127.0.0.1"
API_BIND_PORT = 8000

PRIORITY_BUCKETS = {
    "critical": 0.9,
    "high": 0.7,
    "medium": 0.4
}

# Jira integration
JIRA_BASE_URL = "https://shindep2207.atlassian.net"
JIRA_USER_EMAIL = "shindep2207@gmail.com"
JIRA_API_TOKEN = "ATATT3xFfGF08sWdN5FRior2f6tyzmOyO9568CH8som8DNMUprR_N7jSu-3ERfLx65K6z4-xKNyMCXQee1JFYX1F9-kVV24LKMBj8D46LuLbId03GUQtdG6cTxi_70sEd-kCCcw5xWOKkyqlrEno9T1yusFWZ-FJnjqi48HY3jhHFxbaRpSe8Xo=07F1B12C"
JIRA_PROJECT_KEY = "ADS"

# Email (SMTP) integration
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "shindep2207@gmail.com"
SMTP_PASSWORD = "knwvegqgjqsdqavd"
ALERT_EMAIL_TO = "shindep2207@gmail.com"

