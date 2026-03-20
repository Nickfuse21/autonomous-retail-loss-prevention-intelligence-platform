from src.vision.detector import BaselineBehaviorDetector, SuspiciousEvent
from src.vision.frame_buffer import BufferedFrame, FrameBuffer
from src.vision.schemas import ObservationIn


class VisionPipeline:
    def __init__(self, buffer_size: int = 300) -> None:
        self._buffer = FrameBuffer(max_frames=buffer_size)
        self._detector = BaselineBehaviorDetector()
        self._events: list[SuspiciousEvent] = []

    def ingest_observation(self, observation: ObservationIn) -> SuspiciousEvent | None:
        frame = BufferedFrame(
            source_frame_index=observation.source_frame_index,
            timestamp_utc=observation.timestamp_utc,
            item_sku=observation.item_sku,
            item_visible=observation.item_visible,
            hand_near_item=observation.hand_near_item,
            motion_score=observation.motion_score,
        )
        self._buffer.add(frame)
        event = self._detector.process(frame)
        if event is not None:
            self._events.append(event)
        return event

    def recent_events(self, count: int = 20) -> list[SuspiciousEvent]:
        return self._events[-count:]
