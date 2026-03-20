from pathlib import Path
import os
import shutil
import subprocess


class IncidentClipper:
    def __init__(self, output_dir: str = "data/clips") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_clip(self, incident_id: str, event_timestamp_utc: str, seconds: int = 5) -> str:
        source_video = os.getenv("INCIDENT_SOURCE_VIDEO", "")
        ffmpeg_path = shutil.which("ffmpeg")
        clip_mp4 = self.output_dir / f"{incident_id}.mp4"

        if source_video and Path(source_video).exists() and ffmpeg_path:
            try:
                # For demo reliability we copy a small clip window from source when possible.
                command = [
                    ffmpeg_path,
                    "-y",
                    "-i",
                    source_video,
                    "-t",
                    str(seconds),
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    str(clip_mp4),
                ]
                subprocess.run(command, check=True, capture_output=True, text=True)
                return str(clip_mp4.resolve())
            except subprocess.SubprocessError:
                pass

        clip_file = self.output_dir / f"{incident_id}.txt"
        clip_file.write_text(
            "\n".join(
                [
                    f"incident_id={incident_id}",
                    f"event_timestamp_utc={event_timestamp_utc}",
                    f"clip_seconds={seconds}",
                    "note=Placeholder artifact for simulated incident clip (set INCIDENT_SOURCE_VIDEO + ffmpeg for real mp4 clip).",
                ]
            ),
            encoding="utf-8",
        )
        return str(clip_file.resolve())
