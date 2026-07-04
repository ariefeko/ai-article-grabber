

# Task: Build Daily AI Article Grabber with LangChain RAG Agent, Qdrant, Tavily Fallback, and FastAPI

## Objective

Build a Python application that works as an **AI Article Research Agent**.

The application must:

1. Run daily via cron at 12:00 noon.
2. Grab maximum 5 latest new AI-related articles from RSS feeds.
3. Save each article as a Markdown file.
4. Include article content, images, links, and videos in Markdown.
5. Index saved Markdown articles into **Qdrant**.
6. Use **LangChain** for:

   * document loading
   * text splitting
   * embeddings
   * Qdrant vector store
   * retriever
   * RAG chain
   * simple Agent with tools
7. Use **Tavily** as fallback search when local RAG data is insufficient.
8. Provide **FastAPI** endpoints for ingestion, indexing, asking questions, and listing articles.
9. Allow user to ask questions from CLI Agent and FastAPI.
10. Use structured logging with Python logging.
11. Include helper functions with clear contracts.
12. Include error handling.
13. Include test files.
14. Avoid duplicate article ingestion and duplicate vector indexing.

Current implementation status:

```text
- The base collector, Markdown renderer, Qdrant indexing, RAG chain, tools, CLI, and FastAPI routes exist.
- Default chat model provider is local Ollama.
- Optional OpenAI-compatible chat providers are available through src/llm.py.
- Embeddings still use local Ollama embeddings.
- Tavily is optional and must only run when fallback is explicitly allowed or web search is explicitly requested.
- Runtime data in data/, logs/, and qdrant_storage/ is generated and should not be committed.
```

This project has four main layers:

```text
Layer 1: Article Collector
RSS → Fetch Article → Extract Content/Media → Save Markdown

Layer 2: LangChain RAG
Markdown → Loader → Splitter → Embedding → Qdrant → Retriever

Layer 3: Agent + Fallback
User Question → Local RAG → If fallback allowed and insufficient → Tavily Search → Final Answer

Layer 4: FastAPI
HTTP API → Ingest / Index / Ask / Articles / Sources
```

---

# Tech Stack

Use:

```text
Python 3.11+
FastAPI
Uvicorn

feedparser
requests
beautifulsoup4
readability-lxml
python-dotenv
python-slugify
python-json-logger
pytest
pytest-asyncio
httpx

LangChain
langchain
langchain-community
langchain-text-splitters
langchain-qdrant
langchain-ollama
langchain-openai
qdrant-client

Tavily
tavily-python
```

Use local Ollama models:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

Default models:

```text
Embedding model: nomic-embed-text
Chat model: llama3.1:8b
```

Optional chat providers:

```text
LLM_PROVIDER=local        -> ChatOllama
LLM_PROVIDER=openai       -> ChatOpenAI with OPENAI_API_KEY
LLM_PROVIDER=openagentic  -> ChatOpenAI-compatible endpoint with OPENAGENTIC_* env vars
```

Embeddings remain local Ollama embeddings in the current implementation.

Use Qdrant as vector database.

Do not use Chroma.

---

# Project Structure

Create this structure:

```text
ai-article-grabber/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── docker-compose.yml
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── agent.py
│   ├── api.py
│   ├── config.py
│   ├── logger.py
│   ├── llm.py
│   ├── constants.py
│   ├── types.py
│   ├── exceptions.py
│   ├── collector/
│   │   ├── __init__.py
│   │   ├── rss.py
│   │   ├── fetcher.py
│   │   ├── extractor.py
│   │   ├── markdown.py
│   │   ├── filesystem.py
│   │   ├── url.py
│   │   └── date.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── splitter.py
│   │   ├── vectorstore.py
│   │   ├── retriever.py
│   │   ├── chain.py
│   │   ├── tools.py
│   │   └── indexer.py
│   ├── fallback/
│   │   ├── __init__.py
│   │   └── tavily_search.py
│   └── api/
│       ├── __init__.py
│       ├── schemas.py
│       └── routes.py
├── scripts/
│   └── run_ingest.sh
├── tests/
│   ├── test_rss.py
│   ├── test_extractor.py
│   ├── test_markdown.py
│   ├── test_filesystem.py
│   ├── test_rag_loader.py
│   ├── test_rag_splitter.py
│   ├── test_rag_tools.py
│   ├── test_tavily_fallback.py
│   ├── test_api.py
│   └── fixtures/
│       ├── sample_rss.xml
│       ├── sample_article.html
│       └── sample_article.md
├── data/
│   ├── ingested_urls.txt
│   ├── indexed_files.txt
│   └── articles/
│       └── YYYY-MM-DD/
│           ├── article-title-1.md
│           ├── article-title-2.md
│           └── article-title-3.md
├── logs/
│   └── ingest.log
└── qdrant_storage/
```

Generated files must not be committed:

```text
data/articles/
data/ingested_urls.txt
data/indexed_files.txt
logs/
qdrant_storage/
__pycache__/
.pytest_cache/
.venv/
```

---

# Requirements

## `requirements.txt`

Create:

```text
fastapi
uvicorn[standard]

feedparser
requests
beautifulsoup4
readability-lxml
lxml
python-dotenv
python-slugify
python-json-logger

langchain
langchain-community
langchain-text-splitters
langchain-qdrant
langchain-ollama
langchain-openai
qdrant-client

tavily-python

pytest
pytest-asyncio
httpx
```

---

# Docker Compose

## `docker-compose.yml`

Create Qdrant service:

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: ai-article-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage
```

Run:

```bash
docker compose up -d
```

Qdrant URL:

```text
http://localhost:6333
```

---

# Environment

## `.env.example`

Create:

```env
MAX_ARTICLES=5
OUTPUT_DIR=./data/articles
INGESTED_URLS_FILE=./data/ingested_urls.txt
INDEXED_FILES_FILE=./data/indexed_files.txt
LOG_FILE=./logs/ingest.log
TIMEZONE=Asia/Jakarta
REQUEST_TIMEOUT=20
USER_AGENT=Mozilla/5.0 AIArticleGrabber/1.0
LOG_LEVEL=INFO

OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.1:8b

LLM_PROVIDER=local
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4
OPENAGENTIC_API_KEY=
OPENAGENTIC_MODEL=glm-5
OPENAGENTIC_BASE_URL=https://aimurah.my.id/api/v1

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=ai_articles

RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=150
RAG_RETRIEVER_K=5
RAG_MIN_RELEVANT_DOCS=1

TAVILY_API_KEY=
TAVILY_MAX_RESULTS=5

FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
```

Default behavior:

```text
MAX_ARTICLES=5
OUTPUT_DIR=./data/articles
INGESTED_URLS_FILE=./data/ingested_urls.txt
INDEXED_FILES_FILE=./data/indexed_files.txt
TIMEZONE=Asia/Jakarta
REQUEST_TIMEOUT=20
LOG_LEVEL=INFO

OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.1:8b
LLM_PROVIDER=local

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=ai_articles

RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=150
RAG_RETRIEVER_K=5
RAG_MIN_RELEVANT_DOCS=1

TAVILY_MAX_RESULTS=5

FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
```

Important:

```text
TAVILY_API_KEY is optional for local-only mode.

LLM_PROVIDER defaults to local.
When LLM_PROVIDER=openai, OPENAI_API_KEY is required.
When LLM_PROVIDER=openagentic, OPENAGENTIC_API_KEY is required.

If TAVILY_API_KEY is empty:
- Local RAG must still work.
- Tavily fallback must be disabled gracefully.
- The app must not crash.
```

---

# Git Ignore

## `.gitignore`

Create:

```gitignore
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
.coverage
data/articles/
data/ingested_urls.txt
data/indexed_files.txt
qdrant_storage/
logs/
.DS_Store
```

---

# Constants

## `src/constants.py`

Create:

```python
RSS_FEEDS = [
    "https://venturebeat.com/category/ai/feed/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
]

KEYWORDS = [
    "ai",
    "artificial intelligence",
    "llm",
    "genai",
    "generative ai",
    "machine learning",
    "openai",
    "anthropic",
    "google deepmind",
    "agentic ai",
    "ai agent",
    "large language model",
]
```

---

# Types

## `src/types.py`

Create dataclasses:

```python
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
```

---

# Exceptions

## `src/exceptions.py`

Create:

```python
class AppError(Exception):
    def __init__(self, code: str, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.original_error = original_error
```

Use these error codes:

```text
CONFIG_INVALID
RSS_PARSE_FAILED
FETCH_FAILED
ARTICLE_EMPTY
EXTRACT_FAILED
MARKDOWN_SAVE_FAILED
FILE_READ_FAILED
FILE_WRITE_FAILED
RAG_LOAD_FAILED
RAG_INDEX_FAILED
RAG_RETRIEVE_FAILED
QDRANT_FAILED
TAVILY_FAILED
AGENT_FAILED
API_FAILED
```

---

# Logger

## `src/logger.py`

Use Python logging with JSON format.

Function contract:

```python
def setup_logger(config: AppConfig) -> logging.Logger:
    ...
```

Requirements:

1. Use built-in `logging`.
2. Use `python-json-logger`.
3. Log to stdout.
4. Log to `config.log_file`.
5. Create the log file parent directory automatically.
6. Cron script also redirects stdout/stderr into `logs/ingest.log`.
7. Log format must be structured JSON.
8. Include these fields where relevant:

   * event
   * url
   * count
   * file_path
   * error_code
   * error_message

Implementation hint:

```python
import logging
from pathlib import Path

from pythonjsonlogger.json import JsonFormatter


class AppJsonFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        log_record["time"] = log_record.pop("asctime", None)
        log_record["message"] = record.getMessage()
        log_record["event"] = getattr(record, "event", None)

        for key in list(log_record.keys()):
            if key not in {"time", "message", "event"}:
                log_record.pop(key, None)


def setup_logger(config):
    logger = logging.getLogger("ai_article_grabber")
    logger.setLevel(config.log_level.upper())
    logger.handlers.clear()

    formatter = AppJsonFormatter("%(asctime)s %(message)s %(event)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    log_path = Path(config.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    return logger
```

Required log events:

```text
app.start
app.done
config.invalid

rss.collect.start
rss.collect.done
rss.feed.failed
rss.feed.warning

article.skip.duplicate
article.selected
article.none

article.fetch.start
article.fetch.done
article.fetch.failed
article.fetch.non_html

article.extract.start
article.extract.done
article.content.empty
article.failed
article.unexpected_failed

article.markdown.saved
article.markdown.save_failed

rag.index.start
rag.index.done
rag.index.skip.duplicate
rag.index.failed
rag.documents.loaded
rag.documents.split
rag.vectorstore.updated
rag.retrieve.start
rag.retrieve.done
rag.retrieve.empty

qdrant.connect.start
qdrant.connect.done
qdrant.connect.failed

tavily.search.start
tavily.search.done
tavily.search.failed
tavily.search.disabled

agent.start
agent.question
agent.answer
agent.failed
agent.fallback.used

api.start
api.request
api.error
```

---

# Helper Functions — Collector

## 1. Config Helper

File:

```text
src/config.py
```

Function contract:

```python
def load_config() -> AppConfig:
    ...
```

Responsibilities:

1. Load `.env`.
2. Convert numeric values safely.
3. Apply defaults.
4. Validate numeric values.
5. Allow empty `TAVILY_API_KEY`.
6. Allow empty `QDRANT_API_KEY` for local Qdrant.

Pseudocode:

```text
load_config():
    load .env

    parse:
      MAX_ARTICLES
      REQUEST_TIMEOUT
      RAG_CHUNK_SIZE
      RAG_CHUNK_OVERLAP
      RAG_RETRIEVER_K
      RAG_MIN_RELEVANT_DOCS
      TAVILY_MAX_RESULTS
      FASTAPI_PORT

    if MAX_ARTICLES <= 0:
        raise AppError("CONFIG_INVALID", "MAX_ARTICLES must be greater than 0")

    if REQUEST_TIMEOUT <= 0:
        raise AppError("CONFIG_INVALID", "REQUEST_TIMEOUT must be greater than 0")

    if RAG_CHUNK_SIZE <= 0:
        raise AppError("CONFIG_INVALID", "RAG_CHUNK_SIZE must be greater than 0")

    if RAG_CHUNK_OVERLAP < 0:
        raise AppError("CONFIG_INVALID", "RAG_CHUNK_OVERLAP must be greater than or equal to 0")

    if RAG_RETRIEVER_K <= 0:
        raise AppError("CONFIG_INVALID", "RAG_RETRIEVER_K must be greater than 0")

    if RAG_MIN_RELEVANT_DOCS < 0:
        raise AppError("CONFIG_INVALID", "RAG_MIN_RELEVANT_DOCS must be greater than or equal to 0")

    if TAVILY_MAX_RESULTS <= 0:
        raise AppError("CONFIG_INVALID", "TAVILY_MAX_RESULTS must be greater than 0")

    if FASTAPI_PORT <= 0:
        raise AppError("CONFIG_INVALID", "FASTAPI_PORT must be greater than 0")

    return AppConfig
```

---

## 2. RSS Helper

File:

```text
src/collector/rss.py
```

Function contracts:

```python
def is_ai_related_article(article: CandidateArticle, keywords: list[str]) -> bool:
    ...

def collect_candidate_articles(
    feed_urls: list[str],
    keywords: list[str],
    logger
) -> list[CandidateArticle]:
    ...

def sort_articles_by_newest(
    articles: list[CandidateArticle]
) -> list[CandidateArticle]:
    ...

def remove_duplicate_articles(
    articles: list[CandidateArticle]
) -> list[CandidateArticle]:
    ...
```

Responsibilities:

1. Parse RSS feeds.
2. Extract article title, link, summary, published date.
3. Filter by AI keywords from title and summary.
4. Sort newest first.
5. Remove duplicate URLs.

Pseudocode:

```text
collect_candidate_articles(feed_urls, keywords, logger):
    logger.info event rss.collect.start

    articles = []

    for feed_url in feed_urls:
        try:
            feed = feedparser.parse(feed_url)

            if feed has bozo_exception:
                logger.warning event rss.feed.warning

            for entry in feed.entries:
                title = entry.title or ""
                url = entry.link or ""
                summary = entry.summary or entry.description or ""
                published_at = entry.published or entry.updated or None

                if url is empty:
                    continue

                article = CandidateArticle(
                    title=title,
                    url=url,
                    summary=summary,
                    published_at=published_at,
                    source_feed_url=feed_url
                )

                if is_ai_related_article(article, keywords):
                    articles.append(article)

        except Exception as error:
            logger.error event rss.feed.failed
            continue

    articles = remove_duplicate_articles(articles)
    articles = sort_articles_by_newest(articles)

    logger.info event rss.collect.done

    return articles
```

---

## 3. Fetcher Helper

File:

```text
src/collector/fetcher.py
```

Function contract:

```python
def fetch_html(
    url: str,
    timeout: int,
    user_agent: str,
    logger
) -> str:
    ...
```

Pseudocode:

```text
fetch_html(url, timeout, user_agent, logger):
    logger.info event article.fetch.start

    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": user_agent},
            allow_redirects=True
        )

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")

        if "text/html" not in content_type:
            logger.warning event article.fetch.non_html

        html = response.text

        if html is empty:
            raise AppError("FETCH_FAILED", "Empty HTML response")

        logger.info event article.fetch.done

        return html

    except requests.Timeout as error:
        raise AppError("FETCH_FAILED", "Request timeout", error)

    except requests.RequestException as error:
        raise AppError("FETCH_FAILED", "Request failed", error)
```

---

## 4. URL Helper

File:

```text
src/collector/url.py
```

Function contracts:

```python
def normalize_url(url: str) -> str:
    ...

def absolute_url(base_url: str, maybe_relative_url: str) -> str:
    ...

def get_domain(url: str) -> str:
    ...

def is_valid_http_url(url: str) -> bool:
    ...

def dedupe_media_items(items: list[MediaItem]) -> list[MediaItem]:
    ...
```

Responsibilities:

```text
- Normalize URL.
- Remove URL fragment.
- Convert relative URL to absolute URL.
- Validate http/https URL.
- Extract domain.
- Remove duplicate media/link URLs.
```

---

## 5. Date Helper

File:

```text
src/collector/date.py
```

Function contracts:

```python
def now_iso(timezone: str) -> str:
    ...

def today_date_string(timezone: str) -> str:
    ...

def parse_article_date(date_value: str | None) -> str | None:
    ...
```

Responsibilities:

```text
- Return current datetime in configured timezone.
- Return date folder name YYYY-MM-DD.
- Normalize article published date where possible.
```

---

## 6. Extractor Helper

File:

```text
src/collector/extractor.py
```

Function contracts:

```python
def extract_article(
    html: str,
    candidate: CandidateArticle,
    ingested_at: str
) -> ExtractedArticle:
    ...

def extract_title(
    soup: BeautifulSoup,
    candidate: CandidateArticle
) -> str:
    ...

def extract_published_at(
    soup: BeautifulSoup,
    candidate: CandidateArticle
) -> str | None:
    ...

def extract_content(
    html: str,
    soup: BeautifulSoup
) -> str:
    ...

def extract_images(
    soup: BeautifulSoup,
    base_url: str
) -> list[MediaItem]:
    ...

def extract_links(
    soup: BeautifulSoup,
    base_url: str
) -> list[MediaItem]:
    ...

def extract_videos(
    soup: BeautifulSoup,
    base_url: str
) -> list[MediaItem]:
    ...
```

### Title Extraction Priority

```text
1. RSS candidate title
2. meta[property="og:title"]
3. h1
4. title tag
5. "Untitled Article"
```

### Published Date Extraction Priority

```text
1. RSS candidate published_at
2. meta[property="article:published_time"]
3. meta[name="publish-date"]
4. meta[name="date"]
5. time[datetime]
6. None
```

### Content Extraction Priority

```text
1. readability-lxml summary text
2. article tag text
3. main tag text
4. body text
```

Remove from content:

```text
script
style
noscript
nav
footer
header
aside
form
iframe
```

If extracted content is empty or too short:

```text
Raise AppError("ARTICLE_EMPTY", "Extracted article content is empty")
```

### Image Extraction

Extract from:

```text
img[src]
img[data-src]
img[data-original]
img[srcset]
meta[property="og:image"]
meta[name="twitter:image"]
```

Rules:

```text
- Convert relative URLs to absolute URLs.
- Keep only http/https.
- Avoid duplicate URLs.
- Use alt text if available.
- If alt is missing, use "Article image".
```

### Link Extraction

Extract from:

```text
a[href]
```

Rules:

```text
- Convert relative URLs to absolute URLs.
- Keep only http/https.
- Skip javascript:, mailto:, tel:, and #anchor-only links.
- Avoid duplicate URLs.
- Avoid empty link text.
- If label is empty, use URL.
- Trim label to 120 characters.
```

### Video Extraction

Extract from:

```text
iframe[src]
video[src]
video source[src]
meta[property="og:video"]
meta[property="og:video:url"]
meta[property="og:video:secure_url"]
```

Common video domains:

```text
youtube.com
youtu.be
vimeo.com
player.vimeo.com
dailymotion.com
tiktok.com
```

---

## 7. Filesystem Helper

File:

```text
src/collector/filesystem.py
```

Function contracts:

```python
def ensure_directories(config: AppConfig) -> None:
    ...

def read_ingested_urls(file_path: str) -> set[str]:
    ...

def append_ingested_url(file_path: str, url: str) -> None:
    ...

def read_indexed_files(file_path: str) -> set[str]:
    ...

def append_indexed_file(file_path: str, markdown_file_path: str) -> None:
    ...

def get_output_directory(output_dir: str, date_folder: str) -> str:
    ...

def generate_unique_markdown_path(
    output_directory: str,
    title: str
) -> str:
    ...

def save_text_file(file_path: str, content: str) -> None:
    ...

def list_markdown_files(output_dir: str) -> list[str]:
    ...
```

Responsibilities:

```text
- Create required directories.
- Read already ingested URLs.
- Append successfully ingested URLs.
- Read already indexed Markdown files.
- Append successfully indexed Markdown files.
- Create date-based output folder.
- Generate unique Markdown filename.
- Save Markdown content.
- List Markdown files recursively.
```

---

## 8. Markdown Helper

File:

```text
src/collector/markdown.py
```

Function contracts:

```python
def escape_yaml_value(value: str | None) -> str:
    ...

def html_link(url: str, label: str) -> str:
    ...

def html_image(url: str, alt: str) -> str:
    ...

def render_markdown(article: ExtractedArticle) -> str:
    ...
```

Important:

```text
Markdown does not guarantee open new tab natively.

Therefore:
- links use raw HTML <a target="_blank">
- videos use raw HTML <a target="_blank">
- images are wrapped with raw HTML <a target="_blank"><img /></a>
```

Expected Markdown output:

```markdown
---
title: "Article Title"
source_url: "https://example.com/article"
source_domain: "example.com"
published_at: "2026-07-04T09:30:00"
ingested_at: "2026-07-04T12:00:00+07:00"
---

# Article Title

Source: <a href="https://example.com/article" target="_blank" rel="noopener noreferrer">https://example.com/article</a>  
Published: 2026-07-04T09:30:00  
Ingested: 2026-07-04T12:00:00+07:00  

---

## Content

Article content goes here.

---

## Images

<a href="https://example.com/image.jpg" target="_blank" rel="noopener noreferrer">
  <img src="https://example.com/image.jpg" alt="Article image" />
</a>

---

## Links

- <a href="https://example.com/report" target="_blank" rel="noopener noreferrer">Related AI report</a>

---

## Videos / Embedded Media

- <a href="https://www.youtube.com/embed/example" target="_blank" rel="noopener noreferrer">Embedded video</a>
```

---

# LangChain RAG Helpers with Qdrant

## 1. Markdown Loader

File:

```text
src/rag/loader.py
```

Function contracts:

```python
def parse_frontmatter(markdown_text: str) -> dict:
    ...

def load_markdown_file(file_path: str) -> Document:
    ...

def load_markdown_documents(file_paths: list[str]) -> list[Document]:
    ...
```

Use:

```python
from langchain_core.documents import Document
```

Responsibilities:

```text
- Read Markdown files.
- Parse YAML-like frontmatter manually.
- Preserve full Markdown text as page_content.
- Store metadata:
  - file_path
  - title
  - source_url
  - source_domain
  - published_at
  - ingested_at
```

Pseudocode:

```text
load_markdown_file(file_path):
    read file as UTF-8
    parse frontmatter between first --- and second ---
    content = markdown text
    metadata = parsed frontmatter + file_path
    return Document(page_content=content, metadata=metadata)
```

---

## 2. Text Splitter

File:

```text
src/rag/splitter.py
```

Function contract:

```python
def split_documents(
    documents: list[Document],
    chunk_size: int,
    chunk_overlap: int
) -> list[Document]:
    ...
```

Use:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
```

Pseudocode:

```text
split_documents(documents, chunk_size, chunk_overlap):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    return splitter.split_documents(documents)
```

Default:

```text
chunk_size = 1000
chunk_overlap = 150
```

---

## 3. Qdrant Vector Store

File:

```text
src/rag/vectorstore.py
```

Function contracts:

```python
def create_embeddings(config: AppConfig):
    ...

def get_qdrant_vectorstore(config: AppConfig, logger):
    ...

def add_documents_to_vectorstore(
    config: AppConfig,
    documents: list[Document],
    logger
) -> None:
    ...
```

Use:

```python
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
```

Responsibilities:

```text
- Create Ollama embeddings.
- Connect to Qdrant.
- Create or open Qdrant collection.
- Add split documents to Qdrant.
```

Pseudocode:

```text
create_embeddings(config):
    return OllamaEmbeddings(model=config.ollama_embedding_model)

get_qdrant_vectorstore(config, logger):
    logger.info event qdrant.connect.start

    embeddings = create_embeddings(config)

    client = QdrantClient(
        url=config.qdrant_url,
        api_key=config.qdrant_api_key or None
    )

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=config.qdrant_collection_name,
        embedding=embeddings
    )

    logger.info event qdrant.connect.done

    return vectorstore

add_documents_to_vectorstore(config, documents, logger):
    vectorstore = get_qdrant_vectorstore(config, logger)
    vectorstore.add_documents(documents)
    logger.info event rag.vectorstore.updated count len(documents)
```

Important:

```text
Do not index the same Markdown file repeatedly.
Use data/indexed_files.txt to track indexed file paths.
Only append file path to indexed_files.txt after successful vector store insertion.
```

Do not use Chroma anywhere.

---

## 4. Retriever

File:

```text
src/rag/retriever.py
```

Function contracts:

```python
def get_retriever(config: AppConfig, logger):
    ...

def retrieve_documents(
    question: str,
    config: AppConfig,
    logger
) -> list[Document]:
    ...
```

Pseudocode:

```text
get_retriever(config, logger):
    vectorstore = get_qdrant_vectorstore(config, logger)
    return vectorstore.as_retriever(
        search_kwargs={"k": config.rag_retriever_k}
    )

retrieve_documents(question, config, logger):
    logger.info event rag.retrieve.start

    retriever = get_retriever(config, logger)
    docs = retriever.invoke(question)

    if docs is empty:
        logger.info event rag.retrieve.empty
    else:
        logger.info event rag.retrieve.done count len(docs)

    return docs
```

---

## 5. Tavily Fallback

File:

```text
src/fallback/tavily_search.py
```

Function contracts:

```python
def is_tavily_enabled(config: AppConfig) -> bool:
    ...

def search_tavily(
    query: str,
    config: AppConfig,
    logger
) -> list[TavilySearchResult]:
    ...

def format_tavily_results_for_context(
    results: list[TavilySearchResult]
) -> str:
    ...
```

Use:

```python
from tavily import TavilyClient
```

Responsibilities:

```text
- Check whether TAVILY_API_KEY exists.
- Search Tavily only when fallback is explicitly allowed or external web search is explicitly requested.
- Return title, URL, and content.
- Never crash the app if Tavily fails.
```

Pseudocode:

```text
is_tavily_enabled(config):
    return config.tavily_api_key is not empty

search_tavily(query, config, logger):
    if Tavily API key is empty:
        logger.warning event tavily.search.disabled
        return []

    logger.info event tavily.search.start

    try:
        client = TavilyClient(api_key=config.tavily_api_key)

        response = client.search(
            query=query,
            search_depth="basic",
            max_results=config.tavily_max_results
        )

        results = []

        for item in response["results"]:
            results.append(
                TavilySearchResult(
                    title=item["title"],
                    url=item["url"],
                    content=item["content"]
                )
            )

        logger.info event tavily.search.done count len(results)

        return results

    except Exception as error:
        logger.error event tavily.search.failed
        return []
```

Fallback trigger rules:

```text
Use Tavily fallback only when fallback is allowed and at least one of these is true:
1. Local retriever returns fewer than RAG_MIN_RELEVANT_DOCS documents.
2. Local RAG answer says available article data is not enough.
3. User explicitly asks for latest web information beyond local articles.

FastAPI:
- /ask receives use_fallback.
- use_fallback=false means local-only.
- use_fallback=true allows Tavily if local RAG is insufficient.

CLI:
- local provider uses a deterministic router.
- openai/openagentic providers create a LangChain agent.
- Tavily is used only when the user explicitly asks for web, internet, Tavily, or fallback.
```

Important:

```text
Tavily fallback must be optional.
If TAVILY_API_KEY is missing, answer using local RAG only and mention that web fallback is disabled.
```

---

## 6. RAG Chain with Tavily Fallback

File:

```text
src/rag/chain.py
```

Function contracts:

```python
def format_documents_for_context(documents: list[Document]) -> str:
    ...

def create_local_rag_chain(config: AppConfig, logger):
    ...

def ask_local_rag(
    question: str,
    config: AppConfig,
    logger
) -> RAGAnswer:
    ...

def ask_with_fallback(
    question: str,
    config: AppConfig,
    logger
) -> RAGAnswer:
    ...
```

Use:

```python
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
```

Local RAG prompt:

```text
You are an AI article research assistant.

Answer the user's question using only the provided local article context.

Rules:
- If the context is not enough, say: "The available article data is not enough."
- Keep the answer concise, practical, and clear.
- Mention source URLs when relevant.
- Do not invent facts.
- If multiple articles disagree, explain the difference.

Context:
{context}

Question:
{question}
```

Fallback prompt:

```text
You are an AI article research assistant.

The local article database was not enough, so web fallback results are provided.

Answer the user's question using the provided web fallback context.

Rules:
- Mention that the answer used web fallback.
- Mention source URLs.
- Do not invent facts.
- Keep the answer concise, practical, and clear.

Fallback Context:
{context}

Question:
{question}
```

Pseudocode:

```text
ask_local_rag(question, config, logger):
    docs = retrieve_documents(question, config, logger)

    sources = unique source_url metadata from docs

    if len(docs) < config.rag_min_relevant_docs:
        return RAGAnswer(
            answer="The available article data is not enough.",
            used_fallback=False,
            sources=sources
        )

    context = format_documents_for_context(docs)

    llm = get_chat_llm(config)

    answer = local chain invoke question + context

    return RAGAnswer(
        answer=answer,
        used_fallback=False,
        sources=sources
    )

ask_with_fallback(question, config, logger, use_fallback=False):
    local_answer = ask_local_rag(question, config, logger)

    if local_answer is enough:
        return local_answer

    if use_fallback is false:
        log fallback skipped
        return local_answer

    tavily_results = search_tavily(question, config, logger)

    if tavily_results empty:
        return local_answer

    fallback_context = format_tavily_results_for_context(tavily_results)

    llm = get_chat_llm(config)

    fallback_answer = fallback chain invoke question + fallback_context

    sources = URLs from Tavily results

    return RAGAnswer(
        answer=fallback_answer,
        used_fallback=True,
        sources=sources
    )
```

---

## 7. RAG Tools

File:

```text
src/rag/tools.py
```

Create LangChain tools for the Agent.

Function contracts:

```python
def search_ai_articles_tool(config: AppConfig, logger):
    ...

def list_recent_articles_tool(config: AppConfig):
    ...

def get_article_sources_tool(config: AppConfig, logger):
    ...

def tavily_web_search_tool(config: AppConfig, logger):
    ...

def ingest_external_sources_tool(config: AppConfig, logger):
    ...

def create_agent_tools(config: AppConfig, logger) -> list:
    ...
```

Use:

```python
from langchain_core.tools import Tool
```

Tools required:

## Tool 1: `search_ai_articles`

Purpose:

```text
Search local AI article knowledge base using RAG.
Allow Tavily fallback only when the user explicitly asks for web, internet, Tavily, or fallback.
```

Behavior:

```text
Detect explicit fallback intent.
Call ask_with_fallback(question, config, logger, use_fallback=detected_intent)
```

---

## Tool 2: `list_recent_articles`

Purpose:

```text
List recent saved Markdown articles.
```

Behavior:

```text
Read Markdown files from OUTPUT_DIR.
Parse frontmatter.
Sort by ingested_at descending.
Return top N.
```

---

## Tool 3: `get_article_sources`

Purpose:

```text
Return source URLs from matching local articles.
```

Behavior:

```text
Use retriever to find relevant documents.
Extract metadata source_url.
Return unique URLs.
```

---

## Tool 4: `tavily_web_search`

Purpose:

```text
Search the web using Tavily when the user explicitly asks for latest web info.
```

Behavior:

```text
Call search_tavily(query, config, logger)
Return source URLs and short snippets.
```

---

## Tool 5: `ingest_external_sources`

Purpose:

```text
Search external web sources using Tavily and save selected results as local Markdown files.
Use only when the user explicitly asks to save external sources locally.
```

Behavior:

```text
Parse an optional small limit from the query.
Search Tavily.
Skip source URLs that already exist in local Markdown frontmatter.
Save new Tavily results under OUTPUT_DIR/YYYY-MM-DD/.
Return saved file paths and skipped URLs.
```

---

# RAG Indexer

File:

```text
src/rag/indexer.py
```

Function contract:

```python
def index_markdown_articles(config: AppConfig, logger) -> int:
    ...
```

Responsibilities:

```text
- List Markdown files from OUTPUT_DIR.
- Read indexed files from INDEXED_FILES_FILE.
- Select only Markdown files not yet indexed.
- Load Markdown files into LangChain Documents.
- Split Documents.
- Add chunks to Qdrant vector store.
- Append successfully indexed Markdown file paths into indexed_files.txt.
- Return number of indexed files.
```

Pseudocode:

```text
index_markdown_articles(config, logger):
    logger.info event rag.index.start

    all_files = list_markdown_files(config.output_dir)
    indexed_files = read_indexed_files(config.indexed_files_file)

    new_files = []

    for file_path in all_files:
        if file_path not in indexed_files:
            new_files.append(file_path)
        else:
            logger.info event rag.index.skip.duplicate

    if new_files empty:
        logger.info event rag.index.done count 0
        return 0

    documents = load_markdown_documents(new_files)
    logger.info event rag.documents.loaded count len(documents)

    chunks = split_documents(
        documents,
        config.rag_chunk_size,
        config.rag_chunk_overlap
    )
    logger.info event rag.documents.split count len(chunks)

    add_documents_to_vectorstore(config, chunks, logger)

    for file_path in new_files:
        append_indexed_file(config.indexed_files_file, file_path)

    logger.info event rag.index.done count len(new_files)

    return len(new_files)
```

Error handling:

```text
If one Markdown file fails to load:
    log error
    skip that file
    continue with other files

If Qdrant insertion fails:
    raise AppError("RAG_INDEX_FAILED", ...)
    do not append file paths into indexed_files.txt
```

---

# Agent CLI

## `src/agent.py`

Create an interactive CLI agent.

Command:

```bash
python -m src.agent
```

Responsibilities:

```text
- Load config.
- Setup logger.
- Create LangChain tools.
- Create LangChain Agent when LLM_PROVIDER is openai or openagentic.
- Use deterministic local tool router when LLM_PROVIDER is local.
- Accept user questions from terminal.
- Use local RAG first.
- Use Tavily fallback only when explicitly requested by the user.
- Let user exit with:
  - exit
  - quit
  - q
```

Current LLM provider behavior:

```text
LLM_PROVIDER=local:
- Do not create a LangChain chat agent.
- Route common intents directly to tools.

LLM_PROVIDER=openai:
- Create LangChain agent with ChatOpenAI.
- Require OPENAI_API_KEY.

LLM_PROVIDER=openagentic:
- Create LangChain agent with ChatOpenAI-compatible base_url.
- Require OPENAGENTIC_API_KEY.
```

Agent prompt:

```text
You are an AI Article Research Agent.

Use the available tools when needed to answer questions about collected AI articles.

Rules:
- Prefer search_ai_articles for questions about AI trends, topics, companies, models, or article content.
- Use list_recent_articles when the user asks what articles were collected.
- Use get_article_sources when the user asks for sources or references.
- Use tavily_web_search only when the user explicitly asks for latest web info.
- Do not invent facts.
- If the local knowledge base does not contain enough information and Tavily is unavailable, say so.
- Always mention relevant source URLs when available.
- Keep answers concise and practical.
```

Pseudocode:

```text
main():
    config = load_config()
    logger = setup_logger(config)

    logger.info event agent.start

    tools = create_agent_tools(config, logger)
    provider = LLM_PROVIDER default local

    if provider is openai or openagentic:
        llm = get_chat_llm(config)
        agent = create_agent(model=llm, tools=tools, system_prompt=AGENT_SYSTEM_PROMPT)
    else:
        agent = None

    while True:
        question = input("Ask: ")

        if question.lower() in ["exit", "quit", "q"]:
            break

        logger.info event agent.question

        try:
            if agent exists:
                result = agent.invoke({"messages": [{"role": "user", "content": question}]})
                answer = extract_agent_output(result)
                tool_result = execute_text_tool_call(answer, tools)
                if tool_result is not None:
                    answer = tool_result
            else:
                answer = answer_with_local_router(question, tools)

            print(answer)
            logger.info event agent.answer

        except Exception as error:
            logger.error event agent.failed
            print("Agent failed to answer. Check logs for details.")
```

---

# FastAPI

## `src/api.py`

Create FastAPI app.

Command:

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

Responsibilities:

```text
- Expose health check.
- Trigger ingestion.
- Trigger indexing.
- Ask questions via local RAG chain with optional Tavily fallback.
- List recent Markdown articles.
- Get relevant source URLs.
```

Use:

```python
from fastapi import FastAPI, HTTPException
```

Create app:

```python
app = FastAPI(
    title="AI Article RAG Agent API",
    version="1.0.0",
    description="Daily AI article collector with LangChain RAG, Qdrant, Tavily fallback, and FastAPI."
)
```

---

## API Schemas

File:

```text
src/api/schemas.py
```

Create Pydantic schemas:

```python
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
```

---

## API Routes

File:

```text
src/api/routes.py
```

Required endpoints:

## `GET /health`

Response:

```json
{
  "status": "ok"
}
```

---

## `POST /ingest`

Purpose:

```text
Run article collection and Qdrant indexing.
Same workflow as python -m src.main.
```

Response:

```json
{
  "saved_count": 5,
  "failed_count": 0,
  "indexed_count": 5
}
```

---

## `POST /index`

Purpose:

```text
Index existing Markdown articles into Qdrant.
```

Response:

```json
{
  "indexed_count": 3
}
```

---

## `POST /ask`

Purpose:

```text
Ask the local RAG chain a question.
Use local Qdrant RAG first.
Use Tavily fallback only when use_fallback=true and local RAG is insufficient.
```

Request:

```json
{
  "question": "Apa tren AI terbaru dari artikel yang dikumpulkan?",
  "use_fallback": true
}
```

Response:

```json
{
  "answer": "Jawaban agent...",
  "used_fallback": false,
  "sources": [
    "https://example.com/article"
  ]
}
```

---

## `GET /articles/recent?limit=5`

Purpose:

```text
List recent saved Markdown articles.
```

Response:

```json
[
  {
    "title": "Article Title",
    "source_url": "https://example.com/article",
    "file_path": "data/articles/2026-07-04/article-title.md",
    "published_at": "2026-07-04T09:30:00",
    "ingested_at": "2026-07-04T12:00:00+07:00"
  }
]
```

---

## `GET /sources?query=ai%20agent`

Purpose:

```text
Return relevant source URLs from Qdrant retriever.
```

Response:

```json
{
  "sources": [
    "https://example.com/article-1",
    "https://example.com/article-2"
  ]
}
```

---

## FastAPI Route Pseudocode

```text
POST /ask:
    config = load_config()
    logger = setup_logger(config)

    if request.use_fallback:
        result = ask_with_fallback(request.question, config, logger)
    else:
        result = ask_local_rag(request.question, config, logger)

    return AskResponse(
        answer=result.answer,
        used_fallback=result.used_fallback,
        sources=result.sources
    )
```

Error handling:

```text
- Convert AppError to HTTPException 400 or 500.
- Log all API errors.
- Do not expose raw stack traces.
```

---

# Main Workflow

## `src/main.py`

This is the cron/manual ingestion entrypoint.

Command:

```bash
python -m src.main
```

Responsibilities:

```text
1. Collect latest AI articles.
2. Save new articles as Markdown.
3. Index saved Markdown files into Qdrant using LangChain.
4. Return saved_count, failed_count, indexed_count.
```

Function contracts:

```python
def run_ingestion_pipeline(config: AppConfig, logger) -> tuple[int, int, int]:
    ...

def main() -> None:
    ...
```

Pseudocode:

```text
run_ingestion_pipeline(config, logger):
    ensure_directories(config)

    ingested_urls = read_ingested_urls(config.ingested_urls_file)

    candidates = collect_candidate_articles(
        RSS_FEEDS,
        KEYWORDS,
        logger
    )

    new_candidates = []

    for candidate in candidates:
        normalized_url = normalize_url(candidate.url)

        if normalized_url in ingested_urls:
            logger.info event article.skip.duplicate
            continue

        new_candidates.append(candidate)

        if len(new_candidates) >= config.max_articles:
            break

    if new_candidates empty:
        logger.info event article.none
    else:
        logger.info event article.selected count len(new_candidates)

    date_folder = today_date_string(config.timezone)
    output_directory = get_output_directory(config.output_dir, date_folder)

    saved_count = 0
    failed_count = 0

    for candidate in new_candidates:
        try:
            html = fetch_html(
                candidate.url,
                config.request_timeout,
                config.user_agent,
                logger
            )

            ingested_at = now_iso(config.timezone)

            article = extract_article(
                html=html,
                candidate=candidate,
                ingested_at=ingested_at
            )

            markdown = render_markdown(article)

            file_path = generate_unique_markdown_path(
                output_directory,
                article.title
            )

            save_text_file(file_path, markdown)

            append_ingested_url(
                config.ingested_urls_file,
                normalize_url(candidate.url)
            )

            saved_count += 1

            logger.info event article.markdown.saved

        except AppError as error:
            failed_count += 1
            logger.error event article.failed
            continue

        except Exception as error:
            failed_count += 1
            logger.exception event article.unexpected_failed
            continue

    try:
        indexed_count = index_markdown_articles(config, logger)
    except AppError as error:
        indexed_count = 0
        logger.error event rag.index.failed

    return saved_count, failed_count, indexed_count

main():
    config = load_config()
    logger = setup_logger(config)

    logger.info event app.start

    saved_count, failed_count, indexed_count = run_ingestion_pipeline(config, logger)

    logger.info event app.done saved_count failed_count indexed_count
```

Important:

```text
Even if there are no new articles, index_markdown_articles should still run.

Reason:
There might be existing Markdown files that have not been indexed yet.
```

---

# Error Handling Requirements

The app must not crash just because one article fails.

Rules:

```text
1. If one RSS feed fails:
   - Log error.
   - Continue with other RSS feeds.

2. If one article fails to fetch:
   - Log error.
   - Skip article.
   - Continue with next article.

3. If one article content is empty:
   - Log warning/error.
   - Skip article.
   - Do not save Markdown.
   - Do not append URL to ingested_urls.txt.

4. If Markdown save fails:
   - Log error.
   - Do not append URL to ingested_urls.txt.
   - Continue with next article.

5. If Qdrant indexing fails:
   - Log error.
   - Do not append file path to indexed_files.txt.
   - Collector result should remain saved.
   - Application exits normally after logging failure.

6. If Tavily fails:
   - Log error.
   - Return local RAG answer if available.
   - Do not crash.

7. If Tavily API key is missing:
   - Log tavily.search.disabled.
   - Continue local RAG only.

8. If Agent fails to answer:
   - Log error.
   - Show friendly failure message in CLI.
   - Do not crash interactive session.

9. If FastAPI endpoint fails:
   - Log error.
   - Return controlled HTTP error.

10. If config is invalid:
   - Stop the application.

11. If no new articles:
   - Log info.
   - Still run Qdrant indexing.
   - Exit normally.
```

---

# Cron Script

## `scripts/run_ingest.sh`

Create:

```bash
#!/usr/bin/env bash

set -e

PROJECT_DIR="/absolute/path/to/ai-article-grabber"

cd "$PROJECT_DIR"

mkdir -p logs
mkdir -p data/articles

source .venv/bin/activate

python -m src.main >> logs/ingest.log 2>&1
```

Make executable:

```bash
chmod +x scripts/run_ingest.sh
```

---

# Cron Setup

Run ingestion every day at 12:00 noon.

Open crontab:

```bash
crontab -e
```

Add:

```cron
0 12 * * * /absolute/path/to/ai-article-grabber/scripts/run_ingest.sh
```

Important:

```text
This uses the machine local timezone.
If the machine timezone is Asia/Jakarta, this runs at 12:00 WIB.
```

If server timezone is UTC and target is 12:00 WIB, use:

```cron
0 5 * * * /absolute/path/to/ai-article-grabber/scripts/run_ingest.sh
```

Because:

```text
12:00 WIB = 05:00 UTC
```

Check log:

```bash
tail -f logs/ingest.log
```

---

# CLI Commands

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

docker compose up -d

ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

## Run Collector + Qdrant Indexer

```bash
python -m src.main
```

## Run Agent CLI

```bash
python -m src.agent
```

Example questions:

```text
Apa tren AI terbaru dari artikel yang dikumpulkan?
```

```text
Artikel terbaru membahas OpenAI apa?
```

```text
List 5 artikel terakhir.
```

```text
Berikan source URL tentang AI agent.
```

```text
Ringkas insight utama dari artikel hari ini.
```

## Run FastAPI

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

Open docs:

```text
http://localhost:8000/docs
```

## Run Tests

```bash
pytest
```

---

# Tests

Use `pytest`.

## Test Files

Create:

```text
tests/test_rss.py
tests/test_extractor.py
tests/test_markdown.py
tests/test_filesystem.py
tests/test_rag_loader.py
tests/test_rag_splitter.py
tests/test_rag_tools.py
tests/test_tavily_fallback.py
tests/test_api.py
tests/fixtures/sample_rss.xml
tests/fixtures/sample_article.html
tests/fixtures/sample_article.md
```

---

## `tests/fixtures/sample_rss.xml`

Create sample RSS containing:

```text
- 1 AI article
- 1 non-AI article
- 1 duplicate AI article URL
```

---

## `tests/fixtures/sample_article.html`

Create sample HTML containing:

```text
- title
- meta og:title
- meta article:published_time
- article content
- image with src
- image with data-src
- link with href
- relative link
- iframe YouTube embed
- video source
```

---

## `tests/fixtures/sample_article.md`

Create Markdown containing:

```markdown
---
title: "Sample AI Article"
source_url: "https://example.com/sample-ai-article"
source_domain: "example.com"
published_at: "2026-07-04T09:30:00"
ingested_at: "2026-07-04T12:00:00+07:00"
---

# Sample AI Article

## Content

This article explains how AI agents use retrieval augmented generation.

## Links

- <a href="https://example.com/reference" target="_blank" rel="noopener noreferrer">Reference</a>
```

---

## `tests/test_rss.py`

Test cases:

```text
1. is_ai_related_article returns True for AI keyword in title.
2. is_ai_related_article returns True for AI keyword in summary.
3. is_ai_related_article returns False for unrelated content.
4. remove_duplicate_articles removes duplicate URLs.
5. sort_articles_by_newest puts newer article first.
```

---

## `tests/test_extractor.py`

Test cases:

```text
1. extract_title uses candidate title first.
2. extract_published_at uses candidate published date first.
3. extract_content returns readable article text.
4. extract_images returns absolute image URLs.
5. extract_links returns absolute links and skips invalid links.
6. extract_videos returns iframe/video URLs.
7. extract_article returns ExtractedArticle.
8. extract_article raises AppError if content is empty.
```

---

## `tests/test_markdown.py`

Test cases:

```text
1. render_markdown includes YAML frontmatter.
2. render_markdown includes title.
3. render_markdown includes source URL.
4. render_markdown includes content.
5. render_markdown renders images using <a target="_blank"><img /></a>.
6. render_markdown renders links using <a target="_blank">.
7. render_markdown renders videos using <a target="_blank">.
8. render_markdown writes fallback text when images/links/videos are empty.
```

Required assertions:

```text
target="_blank"
rel="noopener noreferrer"
<img src=
```

---

## `tests/test_filesystem.py`

Test cases:

```text
1. read_ingested_urls returns empty set if file does not exist.
2. read_ingested_urls returns set of URLs.
3. append_ingested_url appends one URL.
4. read_indexed_files returns empty set if file does not exist.
5. append_indexed_file appends one file path.
6. generate_unique_markdown_path creates slug filename.
7. generate_unique_markdown_path appends -2 if filename already exists.
8. save_text_file writes UTF-8 text.
9. list_markdown_files returns Markdown files recursively.
```

---

## `tests/test_rag_loader.py`

Test cases:

```text
1. parse_frontmatter extracts title.
2. parse_frontmatter extracts source_url.
3. load_markdown_file returns LangChain Document.
4. load_markdown_file sets metadata file_path.
5. load_markdown_file keeps Markdown content as page_content.
```

---

## `tests/test_rag_splitter.py`

Test cases:

```text
1. split_documents returns chunks.
2. split_documents preserves metadata.
3. split_documents respects chunk_size.
```

---

## `tests/test_rag_tools.py`

Test cases:

```text
1. create_agent_tools returns required tools.
2. tools include search_ai_articles.
3. tools include list_recent_articles.
4. tools include get_article_sources.
5. tools include tavily_web_search.
```

---

## `tests/test_tavily_fallback.py`

Test cases:

```text
1. is_tavily_enabled returns False when API key is empty.
2. search_tavily returns empty list when API key is missing.
3. search_tavily handles API errors without crashing.
4. format_tavily_results_for_context includes title, URL, and content.
```

Mock Tavily client.

Do not call real Tavily API in unit tests.

---

## `tests/test_api.py`

Use FastAPI TestClient.

Test cases:

```text
1. GET /health returns status ok.
2. POST /ask validates empty question.
3. POST /ask returns answer response shape.
4. GET /articles/recent returns list response shape.
5. GET /sources returns sources response shape.
```

Mock RAG, Qdrant, Tavily, and ingestion pipeline.

Do not call real internet, real Ollama, real Qdrant, or real Tavily in unit tests.

---

# README.md

Create README with:

```text
1. Project purpose.
2. Tech stack.
3. Collector flow.
4. Qdrant RAG flow.
5. Tavily fallback flow.
6. FastAPI flow.
7. Setup instructions.
8. Docker Qdrant setup.
9. Manual run command.
10. Agent CLI command.
11. FastAPI command.
12. Cron setup.
13. Output Markdown format.
14. Qdrant collection information.
15. Log file location.
16. Test command.
17. Known limitations.
```

## Flow Diagram

Include:

```text
Daily Cron at 12:00
   ↓
RSS Feed
   ↓
Latest 5 AI Articles
   ↓
Fetch Article Page
   ↓
Extract Title / Content / Metadata
   ↓
Extract Images as URLs
   ↓
Extract Links as URLs
   ↓
Extract Videos as URLs
   ↓
Render Markdown
   ↓
Save to data/articles/YYYY-MM-DD/
   ↓
LangChain Markdown Loader
   ↓
Text Splitter
   ↓
Ollama Embeddings
   ↓
Qdrant Vector DB
   ↓
Retriever
   ↓
Local RAG Answer
   ↓
If Fallback Allowed and Local Data Is Insufficient
   ↓
Tavily Search Fallback
   ↓
Final Answer
   ↓
FastAPI / CLI
```

---

# Acceptance Criteria

The task is complete when:

```text
- Project structure is created.
- requirements.txt exists.
- .env.example exists.
- .gitignore exists.
- docker-compose.yml exists for Qdrant.
- src/main.py exists and works.
- src/agent.py exists and works.
- src/api.py exists and works.
- src/config.py exists.
- src/logger.py exists.
- src/constants.py exists.
- src/types.py exists.
- src/exceptions.py exists.
- collector helper files exist.
- rag helper files exist.
- fallback/tavily_search.py exists.
- api schemas/routes exist.
- scripts/run_ingest.sh exists and is executable.
- README.md explains how to run the project.
- Running python -m src.main saves article files into data/articles/YYYY-MM-DD/.
- Running python -m src.main also indexes Markdown files into Qdrant.
- Running python -m src.agent starts interactive Agent CLI.
- Running uvicorn src.api:app starts FastAPI.
- GET /health works.
- POST /ingest works.
- POST /index works.
- POST /ask works.
- GET /articles/recent works.
- GET /sources works.
- Each ingest run grabs maximum 5 latest new AI articles.
- Already ingested URLs are skipped.
- Already indexed Markdown files are skipped.
- Failed article does not stop the whole ingestion.
- Failed article URL is not appended to ingested_urls.txt.
- Failed Markdown file is not appended to indexed_files.txt.
- Each Markdown file includes YAML frontmatter.
- Each Markdown file includes title.
- Each Markdown file includes source URL.
- Each Markdown file includes published date if available.
- Each Markdown file includes ingested date.
- Each Markdown file includes article content.
- Each Markdown file includes images as URLs.
- Each Markdown file includes links as URLs.
- Each Markdown file includes videos or embedded media as URLs.
- Image output uses raw HTML with target="_blank".
- Link output uses raw HTML with target="_blank".
- Video output uses raw HTML with target="_blank".
- Logs are structured JSON using Python logging + python-json-logger.
- Logs are written to stdout and LOG_FILE.
- LOG_FILE parent directory is created automatically.
- LangChain is used for document loading, splitting, embeddings, Qdrant vector store, retriever, RAG chain, and Agent tools.
- Qdrant is used instead of Chroma.
- Tavily fallback works when TAVILY_API_KEY is configured.
- Tavily fallback is disabled gracefully when TAVILY_API_KEY is missing.
- Tests exist and pass using pytest.
- Logger tests verify LOG_FILE output.
- Unit tests do not require internet, Ollama, Qdrant, or Tavily.
- Cron is documented to run every day at 12:00 noon.
```

---

# Important Implementation Notes

Keep the implementation simple and predictable.

Do not over-engineer.

Do not use Chroma.

Do not download images locally.

Do not download videos locally.

For this version:

```text
Images = saved as URL in Markdown
Links = saved as URL in Markdown
Videos = saved as URL in Markdown
Markdown files = human-readable knowledge source
Qdrant = RAG search index
Tavily = search fallback
LangChain Agent = reasoning layer with tools
FastAPI = service interface
```

Use raw HTML for open new tab behavior:

```html
<a href="https://example.com" target="_blank" rel="noopener noreferrer">Example</a>
```

For images:

```html
<a href="https://example.com/image.jpg" target="_blank" rel="noopener noreferrer">
  <img src="https://example.com/image.jpg" alt="Article image" />
</a>
```

This makes Markdown compatible with platforms that allow raw HTML.

---

# Future Improvements

Do not implement these now, but mention them in README as possible next steps:

```text
- Telegram or email daily summary
- Streamlit UI
- Content hash duplicate detection
- Article summarization
- Source ranking
- Multi-agent workflow
- GitHub Actions scheduled ingest
- Deployment to VPS or Railway
```
