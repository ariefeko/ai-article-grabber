from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from src.api.routes import ask, health, recent_articles, sources
from src.api.schemas import AskRequest
from src.types import RAGAnswer


def test_health():
    assert health() == {"status": "ok"}


def test_ask_validates_empty_question():
    with pytest.raises(ValidationError):
        AskRequest(question="")


def test_ask_response_shape(monkeypatch: MonkeyPatch):
    monkeypatch.setattr("src.api.routes.load_config", lambda: Mock())
    monkeypatch.setattr("src.api.routes.setup_logger", lambda config: Mock())
    monkeypatch.setattr(
        "src.api.routes.ask_with_fallback",
        lambda question, config, logger, use_fallback=False: RAGAnswer(
            "answer",
            False,
            ["https://e.com"],
        ),
    )
    response = ask(AskRequest(question="What is AI?"))
    assert response.sources == ["https://e.com"]


def test_recent_articles_shape(monkeypatch: MonkeyPatch, tmp_path: Path):
    article = tmp_path / "a.md"
    article.write_text(
        '---\ntitle: "T"\nsource_url: "https://e.com"\ningested_at: "2026-07-04"\n---\nbody',
        encoding="utf-8",
    )
    config = Mock(output_dir=str(tmp_path))
    monkeypatch.setattr("src.api.routes.load_config", lambda: config)
    monkeypatch.setattr("src.api.routes.setup_logger", lambda config: Mock())
    response = recent_articles(limit=5)
    assert isinstance(response, list)


def test_sources_shape(monkeypatch: MonkeyPatch):
    doc = Mock(metadata={"source_url": "https://e.com"})
    monkeypatch.setattr("src.api.routes.load_config", lambda: Mock())
    monkeypatch.setattr("src.api.routes.setup_logger", lambda config: Mock())
    monkeypatch.setattr("src.api.routes.retrieve_documents", lambda query, config, logger: [doc])
    response = sources(query="ai")
    assert response.sources == ["https://e.com"]
