from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from src.api import app
from src.types import RAGAnswer


client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_validates_empty_question():
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_ask_response_shape(monkeypatch: MonkeyPatch):
    monkeypatch.setattr("src.api.routes.load_config", lambda: Mock())
    monkeypatch.setattr("src.api.routes.setup_logger", lambda config: Mock())
    monkeypatch.setattr(
        "src.api.routes.ask_with_fallback",
        lambda question, config, logger: RAGAnswer("answer", False, ["https://e.com"]),
    )
    response = client.post("/ask", json={"question": "What is AI?"})
    assert response.status_code == 200
    assert response.json()["sources"] == ["https://e.com"]


def test_recent_articles_shape(monkeypatch: MonkeyPatch, tmp_path: Path):
    article = tmp_path / "a.md"
    article.write_text(
        '---\ntitle: "T"\nsource_url: "https://e.com"\ningested_at: "2026-07-04"\n---\nbody',
        encoding="utf-8",
    )
    config = Mock(output_dir=str(tmp_path))
    monkeypatch.setattr("src.api.routes.load_config", lambda: config)
    monkeypatch.setattr("src.api.routes.setup_logger", lambda config: Mock())
    response = client.get("/articles/recent")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_sources_shape(monkeypatch: MonkeyPatch):
    doc = Mock(metadata={"source_url": "https://e.com"})
    monkeypatch.setattr("src.api.routes.load_config", lambda: Mock())
    monkeypatch.setattr("src.api.routes.setup_logger", lambda config: Mock())
    monkeypatch.setattr("src.api.routes.retrieve_documents", lambda query, config, logger: [doc])
    response = client.get("/sources", params={"query": "ai"})
    assert response.status_code == 200
    assert response.json() == {"sources": ["https://e.com"]}
