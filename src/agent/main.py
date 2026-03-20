from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.incidents.manager import IncidentManager
from src.vision.detector import SuspiciousEvent
from src.vision.pipeline import VisionPipeline
from src.vision.schemas import ObservationIn, ObservationResponse, SuspiciousEventOut

app = FastAPI(title="Shrinkage Agent Service", version="0.2.0")
pipeline = VisionPipeline()
incident_manager = IncidentManager()
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent", "ui": "enabled"}


def _serialize_event(event: SuspiciousEvent | None) -> SuspiciousEventOut | None:
    if event is None:
        return None
    return SuspiciousEventOut(
        event_id=event.event_id,
        event_type=event.event_type,
        observed_sku=event.observed_sku,
        source_frame_index=event.source_frame_index,
        timestamp_utc=event.timestamp_utc,
        confidence=event.confidence,
        reason=event.reason,
    )


@app.post("/vision/observations", response_model=ObservationResponse)
def ingest_observation(observation: ObservationIn) -> ObservationResponse:
    event = pipeline.ingest_observation(observation)
    if event is not None:
        incident_manager.process_event(event)
    return ObservationResponse(processed=True, event=_serialize_event(event))


@app.get("/vision/events", response_model=list[SuspiciousEventOut])
def list_recent_events() -> list[SuspiciousEventOut]:
    return [_serialize_event(event) for event in pipeline.recent_events() if event is not None]


@app.get("/incidents")
def list_incidents() -> list[dict[str, object]]:
    return [item.model_dump() for item in incident_manager.list_incidents()]


@app.get("/metrics")
def metrics() -> dict[str, int]:
    return incident_manager.metrics()


@app.post("/demo/run")
def run_demo_scenario() -> dict[str, int]:
    now = datetime.now(timezone.utc)
    pattern = [
        {"visible": True, "hand": False, "motion": 0.12},
        {"visible": True, "hand": True, "motion": 0.33},
        {"visible": False, "hand": False, "motion": 0.71},
        {"visible": False, "hand": False, "motion": 0.64},
        {"visible": True, "hand": False, "motion": 0.2},
    ]
    for idx, entry in enumerate(pattern):
        payload = ObservationIn(
            source_frame_index=1000 + idx,
            timestamp_utc=(now + timedelta(seconds=idx)).isoformat(),
            item_sku="sku-apple-001",
            item_visible=entry["visible"],
            hand_near_item=entry["hand"],
            motion_score=entry["motion"],
        )
        event = pipeline.ingest_observation(payload)
        if event is not None:
            incident_manager.process_event(event)
    return {"observations_processed": len(pattern)}
