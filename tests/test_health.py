from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_docs():
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_unauthenticated_customers():
    response = client.get("/api/v1/customers")
    assert response.status_code == 401
    assert response.json()["success"] is False
