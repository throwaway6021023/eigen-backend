from fastapi.testclient import TestClient


def test_health_sync(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == "OK!"
