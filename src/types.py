from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AppConfig:
    max_articles: int
    output_dir: str
    ingested_urls_file: str
    indexed_files_file: str
    log_file: str
    timezone: str
    request_timeout: int
    user_agent: str
    log_level: str

    ollama_embedding_model: str
    ollama_chat_model: str

    qdrant_url: str
    qdrant_api_key: Optional[str]
    qdrant_collection_name: str

    rag_chunk_size: int
    rag_chunk_overlap: int
    rag_retriever_k: int
    rag_min_relevant_docs: int

    tavily_api_key: Optional[str]
    tavily_max_results: int

    fastapi_host: str
    fastapi_port: int


@dataclass
class CandidateArticle:
    title: str
    url: str
    source_feed_url: str
    summary: str = ""
    published_at: Optional[str] = None


@dataclass
class MediaItem:
    url: str
    label: str


@dataclass
class ExtractedArticle:
    title: str
    source_url: str
    source_domain: str
    ingested_at: str
    content: str
    published_at: Optional[str] = None
    images: list[MediaItem] = field(default_factory=list)
    links: list[MediaItem] = field(default_factory=list)
    videos: list[MediaItem] = field(default_factory=list)


@dataclass
class MarkdownArticleMetadata:
    file_path: str
    title: str
    source_url: str
    source_domain: str
    published_at: Optional[str]
    ingested_at: str


@dataclass
class RAGAnswer:
    answer: str
    used_fallback: bool
    sources: list[str] = field(default_factory=list)


@dataclass
class TavilySearchResult:
    title: str
    url: str
    content: str
