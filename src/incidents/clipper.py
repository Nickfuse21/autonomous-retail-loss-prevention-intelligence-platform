from pathlib import Path


class IncidentClipper:
    def __init__(self, output_dir: str = "data/clips") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_clip(self, incident_id: str, event_timestamp_utc: str, seconds: int = 5) -> str:
        clip_file = self.output_dir / f"{incident_id}.txt"
        clip_file.write_text(
            "\n".join(
                [
                    f"incident_id={incident_id}",
                    f"event_timestamp_utc={event_timestamp_utc}",
                    f"clip_seconds={seconds}",
                    "note=Placeholder artifact for simulated incident clip.",
                ]
            ),
            encoding="utf-8",
        )
        return str(clip_file.resolve())
