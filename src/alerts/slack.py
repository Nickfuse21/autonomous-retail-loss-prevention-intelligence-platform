import json
import os
from datetime import datetime, timezone
from pathlib import Path

from src.incidents.models import Incident


class SlackNotifier:
    def __init__(self, outbox_path: str = "data/slack_outbox.jsonl") -> None:
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.outbox_path = Path(outbox_path)
        self.outbox_path.parent.mkdir(parents=True, exist_ok=True)

    def notify(self, incident: Incident) -> str:
        payload = {
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "incident_id": incident.incident_id,
            "status": incident.status,
            "observed_sku": incident.observed_sku,
            "confidence": incident.confidence,
            "decision_reason": incident.decision_reason,
            "clip_path": incident.clip_path,
            "webhook_configured": bool(self.webhook_url),
        }
        with self.outbox_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
        return "queued-local-outbox"
