from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock POS API", version="0.1.0")
TRANSACTIONS: list[dict[str, str]] = []


class ScanIn(BaseModel):
    item_sku: str
    scanned_at: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mock-pos"}


@app.get("/transactions/recent")
def recent_transactions(sku: str | None = None, window_seconds: int = 60) -> dict[str, list[dict[str, str]]]:
    now = datetime.now(timezone.utc)
    filtered: list[dict[str, str]] = []
    for tx in TRANSACTIONS:
        if sku and tx["item_sku"] != sku:
            continue
        try:
            scanned_at = datetime.fromisoformat(tx["scanned_at"].replace("Z", "+00:00"))
        except ValueError:
            continue
        if abs((now - scanned_at).total_seconds()) <= window_seconds:
            filtered.append(tx)
    return {"transactions": filtered}


@app.post("/transactions/scan")
def add_scan(scan: ScanIn) -> dict[str, str]:
    transaction_id = f"tx-{len(TRANSACTIONS) + 1001}"
    scanned_at = scan.scanned_at or datetime.now(timezone.utc).isoformat()
    TRANSACTIONS.append(
        {
            "transaction_id": transaction_id,
            "item_sku": scan.item_sku,
            "scanned_at": scanned_at,
        }
    )
    return {"transaction_id": transaction_id, "item_sku": scan.item_sku, "scanned_at": scanned_at}


@app.delete("/transactions/reset")
def reset_transactions() -> dict[str, bool]:
    TRANSACTIONS.clear()
    return {"ok": True}
