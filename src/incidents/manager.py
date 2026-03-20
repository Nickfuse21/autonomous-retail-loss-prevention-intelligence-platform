from datetime import datetime, timezone
import csv
import io
from uuid import uuid4

from src.alerts.slack import SlackNotifier
from src.incidents.clipper import IncidentClipper
from src.incidents.models import Incident
from src.pos.client import POSClient
from src.vision.behaviors import BehaviorSequenceResult
from src.vision.detector import SuspiciousEvent
from src.vision.reasoning import ReasoningChainBuilder
from src.vision.zones import TrajectoryVerdict


class IncidentManager:
    def __init__(self) -> None:
        self._pos_client = POSClient()
        self._clipper = IncidentClipper()
        self._notifier = SlackNotifier()
        self._reasoning_builder = ReasoningChainBuilder()
        self._incidents: list[Incident] = []

    def process_event(
        self,
        event: SuspiciousEvent,
        behavior_result: BehaviorSequenceResult | None = None,
        zone_verdict: TrajectoryVerdict | None = None,
    ) -> Incident:
        incident_id = f"inc_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
        pos_match = self._pos_client.check_scan_match(
            sku=event.observed_sku,
            observed_at_utc=event.timestamp_utc,
        )

        behavior_conf = behavior_result.pattern_confidence if behavior_result else None
        zone_exit_prob = zone_verdict.exit_probability if zone_verdict else None
        final_confidence = self._compute_combined_confidence(
            event.confidence, behavior_conf, zone_exit_prob, pos_match.matched
        )

        status = "resolved" if pos_match.matched else "escalated"
        clip_path = self._clipper.create_clip(
            incident_id=incident_id,
            event_timestamp_utc=event.timestamp_utc,
            seconds=5,
        )

        chain = self._reasoning_builder.build(
            incident_id=incident_id,
            behavior_explanation=behavior_result.explanation if behavior_result else None,
            behavior_confidence=behavior_conf,
            zone_explanation=zone_verdict.explanation if zone_verdict else None,
            zone_exit_probability=zone_exit_prob,
            pos_matched=pos_match.matched,
            pos_reason=pos_match.reason,
            observed_sku=event.observed_sku,
            final_confidence=final_confidence,
        )

        incident = Incident(
            incident_id=incident_id,
            event_id=event.event_id,
            event_type=event.event_type,
            observed_sku=event.observed_sku,
            observed_at_utc=event.timestamp_utc,
            confidence=round(final_confidence, 3),
            pos_match=pos_match.matched,
            transaction_id=pos_match.transaction_id,
            decision_reason=chain.narrative,
            status=status,
            clip_path=clip_path,
            slack_delivery="pending",
            behavior_pattern=behavior_result.pattern_name if behavior_result else None,
            zone_heading=zone_verdict.heading_toward.value if zone_verdict else None,
            zone_exit_probability=round(zone_exit_prob, 3) if zone_exit_prob is not None else None,
            reasoning_narrative=chain.narrative,
            reasoning_chain=chain.to_dict(),
        )
        delivery = self._notifier.notify(incident)
        incident.slack_delivery = delivery
        self._incidents.append(incident)
        return incident

    def list_incidents(
        self,
        count: int = 50,
        status: str | None = None,
        sku: str | None = None,
        min_confidence: float | None = None,
        max_confidence: float | None = None,
        review_status: str | None = None,
    ) -> list[Incident]:
        items = self._incidents
        if status:
            items = [i for i in items if i.status == status]
        if sku:
            items = [i for i in items if sku.lower() in i.observed_sku.lower()]
        if min_confidence is not None:
            items = [i for i in items if i.confidence >= min_confidence]
        if max_confidence is not None:
            items = [i for i in items if i.confidence <= max_confidence]
        if review_status:
            items = [i for i in items if i.review_status == review_status]
        return items[-count:]

    def update_review(self, incident_id: str, action: str, notes: str | None = None) -> Incident | None:
        incident = next((i for i in self._incidents if i.incident_id == incident_id), None)
        if incident is None:
            return None
        incident.review_action = action
        incident.review_notes = notes
        incident.reviewed_at_utc = datetime.now(timezone.utc).isoformat()
        if action == "approve":
            incident.review_status = "approved"
        elif action == "false_positive":
            incident.review_status = "dismissed"
            incident.status = "resolved"
        elif action == "escalate_security":
            incident.review_status = "escalated_security"
            incident.status = "escalated"
        else:
            incident.review_status = "reviewed"
        return incident

    def export_incidents_csv(
        self,
        status: str | None = None,
        sku: str | None = None,
        review_status: str | None = None,
    ) -> str:
        rows = self.list_incidents(
            count=10000,
            status=status,
            sku=sku,
            review_status=review_status,
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "incident_id",
                "status",
                "review_status",
                "observed_sku",
                "confidence",
                "pos_match",
                "behavior_pattern",
                "zone_heading",
                "observed_at_utc",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.incident_id,
                    row.status,
                    row.review_status,
                    row.observed_sku,
                    row.confidence,
                    row.pos_match,
                    row.behavior_pattern or "",
                    row.zone_heading or "",
                    row.observed_at_utc,
                ]
            )
        return output.getvalue()

    def metrics(self) -> dict[str, int]:
        total = len(self._incidents)
        escalated = len([item for item in self._incidents if item.status == "escalated"])
        resolved = len([item for item in self._incidents if item.status == "resolved"])
        return {
            "total_incidents": total,
            "escalated_incidents": escalated,
            "resolved_incidents": resolved,
        }

    def _compute_combined_confidence(
        self,
        detection_conf: float,
        behavior_conf: float | None,
        zone_exit_prob: float | None,
        pos_matched: bool,
    ) -> float:
        score = detection_conf * 0.4
        if behavior_conf is not None:
            score += behavior_conf * 0.3
        else:
            score += detection_conf * 0.15
        if zone_exit_prob is not None:
            score += zone_exit_prob * 0.2
        else:
            score += 0.1
        if pos_matched:
            score *= 0.3
        else:
            score += 0.1
        return min(0.99, max(0.0, score))
