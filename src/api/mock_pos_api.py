from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI(title="Mock POS API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mock-pos"}


@app.get("/transactions/recent")
def recent_transactions() -> dict[str, list[dict[str, str]]]:
    return {
        "transactions": [
            {
                "transaction_id": "tx-1001",
                "item_sku": "sku-apple-001",
                "scanned_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }
