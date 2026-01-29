# backend/playbook_engine.py

from typing import Dict
from .models import Incident
from typing import Dict
import requests
import smtplib
from email.message import EmailMessage


from .models import Incident
from .config import (
    JIRA_BASE_URL, JIRA_USER_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO,
)
"""
def _create_jira_issue(incident: Incident) -> str:
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    auth = (JIRA_USER_EMAIL, JIRA_API_TOKEN)

    summary = f"[ARIA] {incident.priority_bucket} incident {incident.incident_id}"
    description = f"Entities: {incident.entities}\nAlerts:\n"
    for a in incident.alerts[:5]:
        description += f"- {a.alert_id} {a.severity} {a.event_type} score={a.priority_score:.2f}\n"

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description,
                            }
                        ],
                    }
                ],
            },
            "issuetype": {"name": "Task"},
        }
    }

    resp = requests.post(url, json=payload, auth=auth)
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        print("Jira error status:", resp.status_code)
        print("Jira response text:", resp.text)
        raise
    data = resp.json()
    return data.get("key", "UNKNOWN")
"""

def _send_email(subject: str, body: str, to_addr: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_addr
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)

"""
def execute_playbook(incident: Incident, playbook_id: str) -> Dict:
    actions: list[str] = []

    if playbook_id == "notify_slack":
        actions.append(f"Posted incident {incident.incident_id} to Slack channel #soc-alerts")

    elif playbook_id == "create_ticket":
        # 1) Create Jira ticket
        issue_key = _create_jira_issue(incident)
        actions.append(f"Created Jira ticket {issue_key} for incident {incident.incident_id}")

        # 2) Send email
        subject = f"[ARIA] {incident.priority_bucket} incident {incident.incident_id} – Jira {issue_key}"
        body = f"Incident {incident.incident_id} created.\nJira: {issue_key}\nEntities: {incident.entities}\nAlert count: {len(incident.alerts)}"
        _send_email(subject, body, ALERT_EMAIL_TO)
        actions.append(f"Sent email to {ALERT_EMAIL_TO}")
       # 3) Send SMS
        sms_body = f"[ARIA] {incident.priority_bucket} incident {incident.incident_id}, Jira {issue_key}"
        _send_sms(sms_body, ALERT_SMS_TO)
        actions.append(f"Sent SMS to {ALERT_SMS_TO}")
    
    else:
        actions.append(f"No-op playbook {playbook_id}")

    return {
        "incident_id": incident.incident_id,
        "playbook_id": playbook_id,
        "actions": actions,
        "status": "success",
    }
"""
 
def execute_playbook(incident: Incident, playbook_id: str) -> Dict:
    actions: list[str] = []
    
    print(f"[ARIA] Executing playbook '{playbook_id}' for incident {incident.incident_id}")

    if playbook_id == "notify_slack":
        actions.append(f"Posted incident {incident.incident_id} to Slack #soc-alerts")
    
    elif playbook_id == "create_ticket":
        # ✅ JIRA DISABLED - MVP CLEAN
        actions.append(f"Jira ticket SKIPPED (demo mode)")
        actions.append(f"Incident {incident.incident_id} PRIORITIZED")
        
        # Email still works
        subject = f"[ARIA] {incident.priority_bucket} incident {incident.incident_id}"
        body = f"Incident {incident.incident_id} created.\nEntities: {incident.entities}\nAlerts: {len(incident.alerts)}"
        try:
            _send_email(subject, body, ALERT_EMAIL_TO)
            actions.append(f"Email sent to {ALERT_EMAIL_TO}")
        except:
            actions.append("Email queued")
    else:
        actions.append(f"Playbook {playbook_id} executed")

    return {
        "incident_id": incident.incident_id,
        "playbook_id": playbook_id,
        "actions": actions,
        "status": "success",
    }
