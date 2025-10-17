from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_analyze():
    response = client.post("/analyze", json={"message": "teste"})
    assert response.status_code == 200
