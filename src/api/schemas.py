from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    use_fallback: bool = False


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[str] = []
    used_fallback: bool = False
    fallback_type: str | None = None


class IngestResponse(BaseModel):
    saved_count: int
    failed_count: int
    indexed_count: int


class IndexResponse(BaseModel):
    indexed_count: int


class ArticleItem(BaseModel):
    title: str
    source_url: str
    file_path: str
    published_at: str | None = None
    ingested_at: str | None = None


class SourcesResponse(BaseModel):
    sources: list[str]
