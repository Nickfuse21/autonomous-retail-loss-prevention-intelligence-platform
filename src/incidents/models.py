from pydantic import BaseModel


class Incident(BaseModel):
    incident_id: str
    event_id: str
    event_type: str
    observed_sku: str
    observed_at_utc: str
    confidence: float
    pos_match: bool
    transaction_id: str | None
    decision_reason: str
    status: str
    clip_path: str
    slack_delivery: str
    behavior_pattern: str | None = None
    zone_heading: str | None = None
    zone_exit_probability: float | None = None
    reasoning_narrative: str | None = None
    reasoning_chain: dict[str, object] | None = None
    review_status: str = "unreviewed"
    review_action: str | None = None
    review_notes: str | None = None
    reviewed_at_utc: str | None = None
