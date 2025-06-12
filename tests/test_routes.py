from fastapi.testclient import TestClient

import backend.rag_pipeline.file_ingestion as fi

app = fi.app

client = TestClient(app)


def test_health_endpoint() -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_documents_list(tmp_path, monkeypatch) -> None:
    file_path = tmp_path / "example.txt"
    file_path.write_text("data")
    monkeypatch.setattr(fi, "uploaded_files_dir", tmp_path)
    resp = client.get("/api/documents/list")
    assert resp.status_code == 200
    assert resp.json()["files"] == ["example.txt"]
