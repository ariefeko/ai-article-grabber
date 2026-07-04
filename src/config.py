import os

from dotenv import load_dotenv

from src.exceptions import AppError
from src.types import AppConfig


def _parse_int(name: str, default: int) -> int:
    """Parse an integer environment variable with a default value."""
    raw_value = os.getenv(name, str(default))
    try:
        return int(raw_value)
    except ValueError as error:
        raise AppError("CONFIG_INVALID", f"{name} must be an integer", error) from error


def _optional_env(name: str) -> str | None:
    """Return a stripped environment value or None when unset."""
    value = os.getenv(name, "").strip()
    return value or None


def load_config() -> AppConfig:
    """Load and validate application configuration from environment variables."""
    load_dotenv()

    max_articles = _parse_int("MAX_ARTICLES", 5)
    request_timeout = _parse_int("REQUEST_TIMEOUT", 20)
    rag_chunk_size = _parse_int("RAG_CHUNK_SIZE", 1000)
    rag_chunk_overlap = _parse_int("RAG_CHUNK_OVERLAP", 150)
    rag_retriever_k = _parse_int("RAG_RETRIEVER_K", 5)
    rag_min_relevant_docs = _parse_int("RAG_MIN_RELEVANT_DOCS", 1)
    tavily_max_results = _parse_int("TAVILY_MAX_RESULTS", 5)
    fastapi_port = _parse_int("FASTAPI_PORT", 8000)

    validations = [
        (max_articles > 0, "MAX_ARTICLES must be greater than 0"),
        (request_timeout > 0, "REQUEST_TIMEOUT must be greater than 0"),
        (rag_chunk_size > 0, "RAG_CHUNK_SIZE must be greater than 0"),
        (rag_chunk_overlap >= 0, "RAG_CHUNK_OVERLAP must be greater than or equal to 0"),
        (rag_retriever_k > 0, "RAG_RETRIEVER_K must be greater than 0"),
        (rag_min_relevant_docs >= 0, "RAG_MIN_RELEVANT_DOCS must be greater than or equal to 0"),
        (tavily_max_results > 0, "TAVILY_MAX_RESULTS must be greater than 0"),
        (fastapi_port > 0, "FASTAPI_PORT must be greater than 0"),
    ]
    for is_valid, message in validations:
        if not is_valid:
            raise AppError("CONFIG_INVALID", message)

    return AppConfig(
        max_articles=max_articles,
        output_dir=os.getenv("OUTPUT_DIR", "./data/articles"),
        ingested_urls_file=os.getenv("INGESTED_URLS_FILE", "./data/ingested_urls.txt"),
        indexed_files_file=os.getenv("INDEXED_FILES_FILE", "./data/indexed_files.txt"),
        log_file=os.getenv("LOG_FILE", "./logs/ingest.log"),
        timezone=os.getenv("TIMEZONE", "Asia/Jakarta"),
        request_timeout=request_timeout,
        user_agent=os.getenv("USER_AGENT", "Mozilla/5.0 AIArticleGrabber/1.0"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        ollama_embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        ollama_chat_model=os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b"),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        qdrant_api_key=_optional_env("QDRANT_API_KEY"),
        qdrant_collection_name=os.getenv("QDRANT_COLLECTION_NAME", "ai_articles"),
        rag_chunk_size=rag_chunk_size,
        rag_chunk_overlap=rag_chunk_overlap,
        rag_retriever_k=rag_retriever_k,
        rag_min_relevant_docs=rag_min_relevant_docs,
        tavily_api_key=_optional_env("TAVILY_API_KEY"),
        tavily_max_results=tavily_max_results,
        fastapi_host=os.getenv("FASTAPI_HOST", "0.0.0.0"),
        fastapi_port=fastapi_port,
    )
