# AI Article Grabber

Daily AI article collector and research agent built with Python, LangChain, Qdrant, Tavily fallback, and FastAPI.

The app collects up to 5 latest AI-related RSS articles, saves each article as Markdown, indexes Markdown into Qdrant, and answers questions from local RAG first. Tavily is optional and only used when fallback is explicitly allowed and local article data is insufficient.

## Tech Stack

- Python 3.11+
- FastAPI and Uvicorn
- feedparser, requests, BeautifulSoup, readability-lxml
- LangChain, langchain-qdrant, langchain-ollama, langchain-openai
- Qdrant
- Tavily
- python-json-logger
- pytest

## Flow

```text
Daily Cron at 12:00
   |
RSS Feeds
   |
Latest AI-related Candidate Articles
   |
Fetch Article Page
   |
Extract Title / Content / Metadata
   |
Extract Images / Links / Videos as URLs
   |
Render Markdown
   |
Save to data/articles/YYYY-MM-DD/
   |
LangChain Markdown Loader
   |
Text Splitter
   |
Ollama Embeddings
   |
Qdrant Vector DB
   |
Retriever
   |
Local RAG Answer
   |
If Fallback Allowed and Local Data Is Insufficient
   |
Tavily Search Fallback
   |
Final Answer
   |
FastAPI / CLI
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Install local Ollama models:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

Start Qdrant:

```bash
docker compose up -d
```

Default Qdrant URL:

```text
http://localhost:6333
```

Default collection:

```text
ai_articles
```

## Configuration

The default setup uses local Ollama:

```env
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.1:8b
```

The chat model provider can also be switched through environment variables:

```env
LLM_PROVIDER=local
```

Supported values:

- `local`: uses `ChatOllama` with `OLLAMA_CHAT_MODEL`.
- `openai`: uses `ChatOpenAI` with `OPENAI_API_KEY` and `OPENAI_MODEL`.
- `openagentic`: uses an OpenAI-compatible endpoint with `OPENAGENTIC_API_KEY`, `OPENAGENTIC_MODEL`, and `OPENAGENTIC_BASE_URL`.

Embeddings remain local Ollama embeddings in the current implementation.

## Run Ingestion

```bash
python -m src.main
```

This collects RSS articles, saves Markdown files into `data/articles/YYYY-MM-DD/`, and indexes new Markdown files into Qdrant.

Duplicate protection:

- Ingested URLs are tracked in `data/ingested_urls.txt`.
- Indexed Markdown files are tracked in `data/indexed_files.txt`.

## Agent CLI

```bash
python -m src.agent
```

Example questions:

```text
Apa tren AI terbaru dari artikel yang dikumpulkan?
Artikel terbaru membahas OpenAI apa?
List 5 artikel terakhir.
Berikan source URL tentang AI agent.
Cari internet berita terbaru tentang AI agent.
```

Exit with `exit`, `quit`, or `q`.

CLI behavior:

- With `LLM_PROVIDER=local`, the CLI uses a deterministic router over local tools.
- With `LLM_PROVIDER=openai` or `openagentic`, the CLI creates a LangChain agent with the same tool set.
- Tavily is used only when the question explicitly asks for web or internet fallback.
- External Tavily results can be saved as Markdown through the `ingest_external_sources` tool when the agent is explicitly asked to save external sources locally.

## FastAPI

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

Docs:

```text
http://localhost:8000/docs
```

Endpoints:

- `GET /health`
- `POST /ingest`
- `POST /index`
- `POST /ask`
- `GET /articles/recent?limit=5`
- `GET /sources?query=ai%20agent`

Example ask request:

```json
{
  "question": "Apa insight utama dari artikel AI yang dikumpulkan?",
  "use_fallback": true
}
```

`use_fallback=true` allows Tavily only when local RAG data is insufficient. `use_fallback=false` keeps the answer local-only.

## Tavily Fallback

`TAVILY_API_KEY` is optional.

If it is empty:

- Local RAG still works.
- Tavily fallback is disabled gracefully.
- The app does not crash.

When configured, Tavily can be used by:

- FastAPI `/ask` when `use_fallback=true` and local RAG is insufficient.
- Agent CLI when the user explicitly asks for web or internet information.
- Agent tool `ingest_external_sources` when the user explicitly asks to save external sources locally.

## Markdown Output

Markdown files include YAML frontmatter, source URL, source domain, published date when available, ingested date, content, images, links, and videos as URLs.

Links and images use raw HTML so supported Markdown renderers can open URLs in a new tab:

```html
<a href="https://example.com" target="_blank" rel="noopener noreferrer">Example</a>
```

Images:

```html
<a href="https://example.com/image.jpg" target="_blank" rel="noopener noreferrer">
  <img src="https://example.com/image.jpg" alt="Article image" />
</a>
```

## Logging

Logs use structured JSON through Python logging and `python-json-logger`.

`setup_logger()` writes to both:

- stdout/stderr, useful for local CLI and server logs.
- `LOG_FILE`, which defaults to:

```text
logs/ingest.log
```

The logger creates the log directory automatically when needed. The cron script also appends stdout/stderr to `logs/ingest.log`, so scheduled runs still keep command-level output in the same place.

## Cron

Run every day at 12:00 noon using the machine local timezone:

```cron
0 12 * * * /absolute/path/to/ai-article-grabber/scripts/run_ingest.sh
```

If the server timezone is UTC and the target is 12:00 WIB:

```cron
0 5 * * * /absolute/path/to/ai-article-grabber/scripts/run_ingest.sh
```

Because 12:00 WIB equals 05:00 UTC.

## Tests

```bash
.venv/bin/pytest
```

Current suite:

```text
37 passed
```

Unit tests mock internet, Ollama, Qdrant, Tavily, and file logging dependencies.

## Known Limitations

- Article extraction quality depends on publisher HTML structure.
- RSS feeds may rate-limit or block requests.
- Local RAG quality depends on collected article volume and chat model behavior.
- Qdrant and Ollama must be running for real indexing and local answering.
- OpenAI-compatible chat providers do not replace the Ollama embedding model.

## Future Improvements

- Telegram or email daily summary
- Streamlit UI
- Content hash duplicate detection
- Article summarization
- Source ranking
- Multi-agent workflow
- GitHub Actions scheduled ingest
- Deployment to VPS or Railway
