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
