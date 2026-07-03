from src.rag.tools import create_agent_tools
from src.types import AppConfig


def _config(tmp_path):
    return AppConfig(
        max_articles=5,
        output_dir=str(tmp_path),
        ingested_urls_file=str(tmp_path / "ingested.txt"),
        indexed_files_file=str(tmp_path / "indexed.txt"),
        log_file=str(tmp_path / "log.txt"),
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
        tavily_api_key=None,
        tavily_max_results=5,
        fastapi_host="0.0.0.0",
        fastapi_port=8000,
    )


def test_create_agent_tools_names(tmp_path):
    tools = create_agent_tools(_config(tmp_path), logger=None)
    names = {tool.name for tool in tools}
    assert "search_ai_articles" in names
    assert "list_recent_articles" in names
    assert "get_article_sources" in names
    assert "tavily_web_search" in names
