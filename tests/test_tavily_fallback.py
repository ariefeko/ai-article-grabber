from unittest.mock import Mock, patch

from src.fallback.tavily_search import (
    format_tavily_results_for_context,
    is_tavily_enabled,
    search_tavily,
)
from src.types import AppConfig, TavilySearchResult


def _config(api_key=None):
    return AppConfig(
        max_articles=5,
        output_dir="./data/articles",
        ingested_urls_file="./data/ingested_urls.txt",
        indexed_files_file="./data/indexed_files.txt",
        log_file="./logs/ingest.log",
        timezone="Asia/Jakarta",
        request_timeout=20,
        user_agent="test",
        log_level="INFO",
        ollama_embedding_model="nomic-embed-text",
        ollama_chat_model="llama3.1:8b",
        qdrant_url="http://localhost:6333",
        qdrant_api_key=None,
        qdrant_collection_name="ai_articles",
        rag_chunk_size=1000,
        rag_chunk_overlap=150,
        rag_retriever_k=5,
        rag_min_relevant_docs=1,
        tavily_api_key=api_key,
        tavily_max_results=5,
        fastapi_host="0.0.0.0",
        fastapi_port=8000,
    )


def test_is_tavily_enabled_false():
    assert not is_tavily_enabled(_config())


def test_search_tavily_missing_key_empty():
    logger = Mock()
    assert search_tavily("ai", _config(), logger) == []
    logger.warning.assert_called()


@patch("src.fallback.tavily_search.TavilyClient")
def test_search_tavily_handles_errors(mock_client):
    mock_client.side_effect = RuntimeError("boom")
    assert search_tavily("ai", _config("key"), Mock()) == []


def test_format_tavily_results_for_context():
    text = format_tavily_results_for_context([TavilySearchResult("Title", "https://e.com", "Content")])
    assert "Title" in text
    assert "https://e.com" in text
    assert "Content" in text
