from fastapi.testclient import TestClient

from src.agent.main import app as agent_app


def test_incident_review_and_filter_and_export() -> None:
    client = TestClient(agent_app)

    demo = client.post("/demo/run")
    assert demo.status_code == 200

    incidents_resp = client.get("/incidents")
    assert incidents_resp.status_code == 200
    incidents = incidents_resp.json()
    assert len(incidents) >= 1
    incident_id = incidents[-1]["incident_id"]

    review_resp = client.post(
        f"/incidents/{incident_id}/review",
        json={"action": "approve", "notes": "verified by manager"},
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["ok"] is True
    assert review_resp.json()["incident"]["review_status"] == "approved"

    filtered = client.get("/incidents", params={"review_status": "approved"})
    assert filtered.status_code == 200
    approved = filtered.json()
    assert any(item["incident_id"] == incident_id for item in approved)

    csv_resp = client.get("/incidents/export.csv", params={"review_status": "approved"})
    assert csv_resp.status_code == 200
    assert "incident_id,status,review_status" in csv_resp.text
    assert incident_id in csv_resp.text
