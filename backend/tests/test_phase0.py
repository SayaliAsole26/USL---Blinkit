from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["phase"] == "3"
    assert "Dataset" in data["framework"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_feature_flags():
    response = client.get("/v1/flags")
    assert response.status_code == 200
    data = response.json()
    assert "usl_enabled" in data
    assert "usl_checkout_recommendations" in data


def test_groq_smoke_without_key():
    response = client.post("/v1/integrations/groq/smoke")
    assert response.status_code == 200
    assert "ok" in response.json()
