from dataclasses import dataclass
from uuid import uuid4

from src.vision.frame_buffer import BufferedFrame


@dataclass(frozen=True)
class SuspiciousEvent:
    event_id: str
    event_type: str
    observed_sku: str
    source_frame_index: int
    timestamp_utc: str
    confidence: float
    reason: str


class BaselineBehaviorDetector:
    def __init__(
        self,
        disappearance_window_frames: int = 8,
        hand_proximity_window_frames: int = 12,
        cooldown_frames: int = 20,
        min_motion_score: float = 0.25,
    ) -> None:
        self.disappearance_window_frames = disappearance_window_frames
        self.hand_proximity_window_frames = hand_proximity_window_frames
        self.cooldown_frames = cooldown_frames
        self.min_motion_score = min_motion_score

        self._last_visible_frame_index: int | None = None
        self._last_hand_near_item_frame_index: int | None = None
        self._last_alert_frame_index: int | None = None

    def process(self, frame: BufferedFrame) -> SuspiciousEvent | None:
        if frame.hand_near_item:
            self._last_hand_near_item_frame_index = frame.source_frame_index

        if frame.item_visible:
            self._last_visible_frame_index = frame.source_frame_index
            return None

        if self._last_visible_frame_index is None:
            return None

        recently_disappeared = (
            frame.source_frame_index - self._last_visible_frame_index
            <= self.disappearance_window_frames
        )
        hand_was_recent = self._last_hand_near_item_frame_index is not None and (
            frame.source_frame_index - self._last_hand_near_item_frame_index
            <= self.hand_proximity_window_frames
        )
        enough_motion = frame.motion_score >= self.min_motion_score

        if not (recently_disappeared and hand_was_recent and enough_motion):
            return None

        if self._last_alert_frame_index is not None:
            frame_delta = frame.source_frame_index - self._last_alert_frame_index
            in_cooldown = 0 <= frame_delta <= self.cooldown_frames
            if in_cooldown:
                return None

        self._last_alert_frame_index = frame.source_frame_index
        confidence = min(0.99, 0.5 + (frame.motion_score * 0.49))
        return SuspiciousEvent(
            event_id=f"evt_{uuid4().hex[:12]}",
            event_type="suspected_item_disappearance",
            observed_sku=frame.item_sku,
            source_frame_index=frame.source_frame_index,
            timestamp_utc=frame.timestamp_utc,
            confidence=round(confidence, 3),
            reason="Item disappeared shortly after hand proximity without recovery.",
        )
