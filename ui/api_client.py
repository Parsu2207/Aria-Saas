# ui/api_client.py
import requests


class ApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url

    def get_alerts(self, priority: str | None = None):
        params = {}
        if priority:
            params["priority"] = priority
        r = requests.get(f"{self.base_url}/api/v1/alerts", params=params, timeout=5)
        r.raise_for_status()
        return r.json()

    def get_incidents(self):
        r = requests.get(f"{self.base_url}/api/v1/incidents", timeout=5)
        r.raise_for_status()
        return r.json()

    def run_playbook(self, playbook_id: str, incident_id: str):
        r = requests.post(
            f"{self.base_url}/api/v1/playbooks/{playbook_id}",
            params={"incident_id": incident_id},
            timeout=5
        )
        r.raise_for_status()
        return r.json()
