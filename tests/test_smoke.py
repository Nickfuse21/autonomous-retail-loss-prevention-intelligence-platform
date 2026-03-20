from fastapi.testclient import TestClient

from src.agent.main import app as agent_app
from src.api.mock_pos_api import app as pos_app


def test_agent_health() -> None:
    response = TestClient(agent_app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_mock_pos_health() -> None:
    response = TestClient(pos_app).get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "mock-pos"
