from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from src.rag.tools import should_use_external_fallback

from src.api.schemas import (
    ArticleItem,
    AskRequest,
    AskResponse,
    IndexResponse,
    IngestResponse,
    SourcesResponse,
)
from src.collector.filesystem import list_markdown_files
from src.config import load_config
from src.exceptions import AppError
from src.logger import setup_logger
from src.main import run_ingestion_pipeline
from src.rag.chain import ask_local_rag, ask_with_fallback
from src.rag.indexer import index_markdown_articles
from src.rag.loader import load_markdown_file
from src.rag.retriever import retrieve_documents

router = APIRouter()


def _config_logger():
    """Load request-scoped configuration and logger instances."""
    config = load_config()
    logger = setup_logger(config)
    return config, logger


def _handle_error(error: Exception, logger):
    """Convert application errors into FastAPI HTTP exceptions."""
    if isinstance(error, AppError):
        status_code = 400 if error.code == "CONFIG_INVALID" else 500
        logger.error(
            "API app error",
            extra={
                "event": "api.error",
                "error_code": error.code,
                "error_message": error.message,
            },
        )
        raise HTTPException(status_code=status_code, detail={"code": error.code, "message": error.message})
    logger.error(
        "API failed",
        extra={
            "event": "api.error",
            "error_code": "API_FAILED",
            "error_message": str(error),
        },
    )
    raise HTTPException(status_code=500, detail={"code": "API_FAILED", "message": "Request failed"})


def _metadata_text(
    metadata: Mapping[str, Any] | None,
    key: str,
    default: str = "",
) -> str:
    """Read a metadata value as text with a default fallback."""
    if not isinstance(metadata, Mapping):
        return default

    value = metadata.get(key)
    if value is None:
        return default

    return str(value)


def _metadata_optional_text(
    metadata: Mapping[str, Any] | None,
    key: str,
) -> str | None:
    """Read a metadata value as optional text."""
    value = _metadata_text(metadata, key)
    return value or None


@router.get("/health")
def health():
    """Return the API health status."""
    return {"status": "ok"}


@router.post("/ingest", response_model=IngestResponse)
def ingest():
    """Run article ingestion and indexing from the API."""
    config, logger = _config_logger()
    logger.info("API ingest request", extra={"event": "api.request"})
    try:
        saved_count, failed_count, indexed_count = run_ingestion_pipeline(config, logger)
        return IngestResponse(
            saved_count=saved_count,
            failed_count=failed_count,
            indexed_count=indexed_count,
        )
    except Exception as error:
        _handle_error(error, logger)


@router.post("/index", response_model=IndexResponse)
def index():
    """Index saved Markdown articles from the API."""
    config, logger = _config_logger()
    logger.info("API index request", extra={"event": "api.request"})
    try:
        return IndexResponse(indexed_count=index_markdown_articles(config, logger))
    except Exception as error:
        _handle_error(error, logger)


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Answer a question using local RAG and optional explicit fallback."""
    config, logger = _config_logger()
    logger.info("API ask request", extra={"event": "api.request"})
    try:
        use_external_fallback = (
            request.use_fallback
            and should_use_external_fallback(request.question)
        )

        result = (
            ask_with_fallback(
                request.question,
                config,
                logger,
                use_fallback=True,
            )
            if use_external_fallback
            else ask_local_rag(request.question, config, logger)
        )

        return AskResponse(
            question=request.question,
            answer=result.answer,
            sources=result.sources,
            used_fallback=result.used_fallback,
            fallback_type="tavily" if result.used_fallback else None,
        )
    except Exception as error:
        _handle_error(error, logger)


@router.get("/articles/recent", response_model=list[ArticleItem])
def recent_articles(limit: int = Query(default=5, ge=1, le=100)):
    """Return recently saved articles from local Markdown files."""
    config, logger = _config_logger()
    logger.info("API recent articles request", extra={"event": "api.request"})
    try:
        items: list[ArticleItem] = []
        for file_path in list_markdown_files(config.output_dir):
            document = load_markdown_file(file_path)
            metadata = document.metadata
            items.append(
                ArticleItem(
                    title=_metadata_text(metadata, "title", "Untitled"),
                    source_url=_metadata_text(metadata, "source_url"),
                    file_path=file_path,
                    published_at=_metadata_optional_text(metadata, "published_at"),
                    ingested_at=_metadata_optional_text(metadata, "ingested_at"),
                )
            )
        items.sort(key=lambda item: item.ingested_at or "", reverse=True)
        return items[:limit]
    except Exception as error:
        _handle_error(error, logger)


@router.get("/sources", response_model=SourcesResponse)
def sources(query: str = Query(..., min_length=1)):
    """Return source URLs for documents matching a query."""
    config, logger = _config_logger()
    logger.info("API sources request", extra={"event": "api.request"})
    try:
        documents = retrieve_documents(query, config, logger)
        seen: set[str] = set()
        source_urls: list[str] = []
        for document in documents:
            source_url = _metadata_optional_text(document.metadata, "source_url")
            if source_url and source_url not in seen:
                seen.add(source_url)
                source_urls.append(source_url)
        return SourcesResponse(sources=source_urls)
    except Exception as error:
        _handle_error(error, logger)
