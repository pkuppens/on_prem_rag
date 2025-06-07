from fastapi.testclient import TestClient

from auth_service.main import app

client = TestClient(app)


def test_register_and_login() -> None:
    resp = client.post("/register", json={"username": "alice", "email": "a@example.com", "password": "secret"})
    assert resp.status_code == 200
    token_resp = client.post("/login", json={"username": "alice", "password": "secret"})
    assert token_resp.status_code == 200
    token = token_resp.json()["token"]
    me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "alice"
