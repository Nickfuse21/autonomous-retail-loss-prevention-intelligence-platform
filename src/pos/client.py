import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx


@dataclass(frozen=True)
class POSMatchResult:
    matched: bool
    transaction_id: str | None
    reason: str


class POSClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: float = 3.0) -> None:
        self.base_url = base_url or os.getenv("POS_API_URL", "http://localhost:8081")
        self.timeout_seconds = timeout_seconds

    def check_scan_match(self, sku: str, observed_at_utc: str, window_seconds: int = 60) -> POSMatchResult:
        try:
            observed_at = datetime.fromisoformat(observed_at_utc.replace("Z", "+00:00"))
        except ValueError:
            observed_at = datetime.now(timezone.utc)
        lower_bound = observed_at - timedelta(seconds=window_seconds)
        upper_bound = observed_at + timedelta(seconds=window_seconds)

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(
                    f"{self.base_url}/transactions/recent",
                    params={"sku": sku, "window_seconds": window_seconds},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return POSMatchResult(
                matched=False,
                transaction_id=None,
                reason=f"POS service unavailable: {exc.__class__.__name__}",
            )

        transactions = payload.get("transactions", [])
        for transaction in transactions:
            scanned_raw = transaction.get("scanned_at")
            if not scanned_raw:
                continue
            try:
                scanned_at = datetime.fromisoformat(scanned_raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if lower_bound <= scanned_at <= upper_bound:
                return POSMatchResult(
                    matched=True,
                    transaction_id=transaction.get("transaction_id"),
                    reason="Matching POS scan found in time window.",
                )

        return POSMatchResult(
            matched=False,
            transaction_id=None,
            reason="No matching POS scan found in configured time window.",
        )
