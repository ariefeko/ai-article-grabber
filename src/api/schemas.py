from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    use_fallback: bool = True


class AskResponse(BaseModel):
    answer: str
    used_fallback: bool
    sources: list[str]


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
