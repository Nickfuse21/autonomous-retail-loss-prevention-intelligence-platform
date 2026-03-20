from datetime import datetime, timezone
from uuid import uuid4

from src.alerts.slack import SlackNotifier
from src.incidents.clipper import IncidentClipper
from src.incidents.models import Incident
from src.pos.client import POSClient
from src.vision.detector import SuspiciousEvent


class IncidentManager:
    def __init__(self) -> None:
        self._pos_client = POSClient()
        self._clipper = IncidentClipper()
        self._notifier = SlackNotifier()
        self._incidents: list[Incident] = []

    def process_event(self, event: SuspiciousEvent) -> Incident:
        incident_id = f"inc_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
        pos_match = self._pos_client.check_scan_match(
            sku=event.observed_sku,
            observed_at_utc=event.timestamp_utc,
        )
        status = "resolved" if pos_match.matched else "escalated"
        clip_path = self._clipper.create_clip(
            incident_id=incident_id,
            event_timestamp_utc=event.timestamp_utc,
            seconds=5,
        )
        incident = Incident(
            incident_id=incident_id,
            event_id=event.event_id,
            event_type=event.event_type,
            observed_sku=event.observed_sku,
            observed_at_utc=event.timestamp_utc,
            confidence=event.confidence,
            pos_match=pos_match.matched,
            transaction_id=pos_match.transaction_id,
            decision_reason=pos_match.reason,
            status=status,
            clip_path=clip_path,
            slack_delivery="pending",
        )
        delivery = self._notifier.notify(incident)
        incident.slack_delivery = delivery
        self._incidents.append(incident)
        return incident

    def list_incidents(self, count: int = 50) -> list[Incident]:
        return self._incidents[-count:]

    def metrics(self) -> dict[str, int]:
        total = len(self._incidents)
        escalated = len([item for item in self._incidents if item.status == "escalated"])
        resolved = len([item for item in self._incidents if item.status == "resolved"])
        return {
            "total_incidents": total,
            "escalated_incidents": escalated,
            "resolved_incidents": resolved,
        }
