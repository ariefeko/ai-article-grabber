# AI Article Grabber

Daily AI article collector and research agent built with Python, LangChain, Qdrant, Tavily fallback, and FastAPI.

The app collects up to 5 latest AI-related RSS articles, saves each article as Markdown, indexes Markdown into Qdrant, and answers questions from local RAG first. Tavily can be used as optional web fallback when local data is insufficient.

## Tech Stack

- Python 3.11+
- FastAPI and Uvicorn
- feedparser, requests, BeautifulSoup, readability-lxml
- LangChain, langchain-qdrant, langchain-ollama
- Qdrant
- Tavily
- python-json-logger
- pytest

## Flow

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
If Local Data Insufficient
   ↓
Tavily Search Fallback
   ↓
Final Agent Answer
   ↓
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

## Run Ingestion

```bash
python -m src.main
```

This collects RSS articles, saves Markdown files into `data/articles/YYYY-MM-DD/`, and indexes unindexed Markdown files into Qdrant.

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
Ringkas insight utama dari artikel hari ini.
```

Exit with `exit`, `quit`, or `q`.

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

## Tavily Fallback

`TAVILY_API_KEY` is optional.

If it is empty:

- Local RAG still works.
- Tavily fallback is disabled gracefully.
- The app does not crash.

When configured, Tavily is used if local retriever data is insufficient, the local answer says the data is not enough, or the user asks for latest web information.

## Markdown Output

Markdown files include YAML frontmatter, source URL, published date when available, ingested date, content, images, links, and videos as URLs.

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

Cron redirects stdout/stderr to:

```text
logs/ingest.log
```

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
pytest
```

Unit tests mock internet, Ollama, Qdrant, and Tavily dependencies.

## Known Limitations

- Article extraction quality depends on publisher HTML structure.
- RSS feeds may rate-limit or block requests.
- Local RAG quality depends on collected article volume and Ollama model behavior.
- Qdrant and Ollama must be running for real indexing and answering.

## Future Improvements

- Telegram or email daily summary
- Streamlit UI
- Content hash duplicate detection
- Article summarization
- Source ranking
- Multi-agent workflow
- GitHub Actions scheduled ingest
- Deployment to VPS or Railway
