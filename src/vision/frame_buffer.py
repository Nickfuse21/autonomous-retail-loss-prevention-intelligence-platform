from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class BufferedFrame:
    source_frame_index: int
    timestamp_utc: str
    item_sku: str
    item_visible: bool
    hand_near_item: bool
    motion_score: float


class FrameBuffer:
    def __init__(self, max_frames: int) -> None:
        if max_frames <= 0:
            raise ValueError("max_frames must be > 0")
        self._frames: deque[BufferedFrame] = deque(maxlen=max_frames)

    def add(self, frame: BufferedFrame) -> None:
        self._frames.append(frame)

    def recent(self, count: int) -> list[BufferedFrame]:
        if count <= 0:
            return []
        return list(self._frames)[-count:]

    def all(self) -> list[BufferedFrame]:
        return list(self._frames)
