from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Request body for asking a question through the API."""
    question: str = Field(..., min_length=1)
    use_fallback: bool = False


class AskResponse(BaseModel):
    """Response body for an answered API question."""
    question: str
    answer: str
    sources: list[str] = []
    used_fallback: bool = False
    fallback_type: str | None = None


class IngestResponse(BaseModel):
    """Response body for an ingestion run."""
    saved_count: int
    failed_count: int
    indexed_count: int


class IndexResponse(BaseModel):
    """Response body for an indexing run."""
    indexed_count: int


class ArticleItem(BaseModel):
    """Serialized metadata for a saved article."""
    title: str
    source_url: str
    file_path: str
    published_at: str | None = None
    ingested_at: str | None = None


class SourcesResponse(BaseModel):
    """Response body containing matching source URLs."""
    sources: list[str]

