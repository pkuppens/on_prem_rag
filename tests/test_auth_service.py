from pathlib import Path

from fastapi.testclient import TestClient

from auth_service.main import app

# Remove the SQLite database between test runs to ensure a clean state
DB_PATH = Path(__file__).resolve().parents[1] / "src" / "auth_service" / "auth.db"


def test_register_and_login() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    with TestClient(app) as client:
        resp = client.post(
            "/register",
            json={"username": "alice", "email": "a@example.com", "password": "secret"},
        )
        assert resp.status_code == 200
        token_resp = client.post(
            "/login",
            json={"username": "alice", "password": "secret"},
        )
        assert token_resp.status_code == 200
        token = token_resp.json()["token"]
        me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["username"] == "alice"
