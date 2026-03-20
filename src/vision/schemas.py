from pydantic import BaseModel, Field


class ObservationIn(BaseModel):
    source_frame_index: int = Field(ge=0)
    timestamp_utc: str
    item_sku: str = "sku-apple-001"
    item_visible: bool
    hand_near_item: bool
    motion_score: float = Field(ge=0.0, le=1.0)


class SuspiciousEventOut(BaseModel):
    event_id: str
    event_type: str
    observed_sku: str
    source_frame_index: int
    timestamp_utc: str
    confidence: float
    reason: str


class ObservationResponse(BaseModel):
    processed: bool
    event: SuspiciousEventOut | None
