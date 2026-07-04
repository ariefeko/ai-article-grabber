from datetime import datetime, timezone
from pathlib import Path
import re

from langchain_core.tools import Tool

from src.collector.filesystem import list_markdown_files
from src.fallback.tavily_search import search_tavily
from src.rag.chain import ask_with_fallback
from src.rag.loader import load_markdown_file, parse_frontmatter
from src.rag.retriever import retrieve_documents
from src.types import AppConfig


def should_use_external_fallback(question: str) -> bool:
    """Return whether a question explicitly asks for external web fallback."""
    normalized = question.lower()

    explicit_keywords = [
        "tavily",
        "web search",
        "search web",
        "cari web",
        "cari di web",
        "cari internet",
        "di internet",
        "dari internet",
        "pakai internet",
        "gunakan internet",
        "pakai web",
        "gunakan web",
        "resource luar",
        "sumber luar",
        "external source",
        "external sources",
        "fallback",
        "gunakan fallback",
        "pakai fallback",
        "latest web",
        "info terbaru dari internet",
        "berita terbaru dari internet",
    ]

    return any(keyword in normalized for keyword in explicit_keywords)


def _slugify(value: str) -> str:
    """Convert text into a filesystem-friendly slug."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "external-source"


def _escape_frontmatter(value: str) -> str:
    """Escape text for quoted Markdown frontmatter values."""
    return value.replace('"', '\\"').replace("\n", " ").strip()


def _parse_limit_from_query(query: str, default: int = 3, maximum: int = 5) -> int:
    """Parse and clamp a result limit from a tool query."""
    match = re.search(r"\b(\d{1,2})\b", query)
    if not match:
        return default

    limit = int(match.group(1))
    return max(1, min(limit, maximum))


def _existing_source_urls(config: AppConfig) -> set[str]:
    """Collect source URLs that are already saved as local Markdown files."""
    urls: set[str] = set()

    for file_path in list_markdown_files(config.output_dir):
        try:
            metadata = parse_frontmatter(Path(file_path).read_text(encoding="utf-8"))
            source_url = metadata.get("source_url")
            if source_url:
                urls.add(source_url)
        except Exception:
            continue

    return urls


def search_ai_articles_tool(config: AppConfig, logger):
    """Create a tool for answering questions from local AI articles."""
    def _run(question: str) -> str:
        """Run local article search with explicit fallback detection."""
        use_fallback = should_use_external_fallback(question)

        result = ask_with_fallback(
            question,
            config,
            logger,
            use_fallback=use_fallback,
        )

        sources = "\n".join(result.sources)
        return f"{result.answer}\n\nSources:\n{sources}" if sources else result.answer

    return Tool(
        name="search_ai_articles",
        description=(
            "Search local AI article knowledge base using RAG. "
            "External Tavily fallback is only used when explicitly requested."
        ),
        func=_run,
    )


def list_recent_articles_tool(config: AppConfig):
    """Create a tool for listing recently saved article metadata."""
    def _run(limit_text: str = "5") -> str:
        """Return recent saved articles up to the requested limit."""
        try:
            limit = int(str(limit_text).strip() or "5")
        except ValueError:
            limit = 5

        items: list[dict] = []

        for file_path in list_markdown_files(config.output_dir):
            try:
                document = load_markdown_file(file_path)
                metadata = document.metadata
            except Exception:
                metadata = parse_frontmatter(Path(file_path).read_text(encoding="utf-8"))
                metadata["file_path"] = file_path

            items.append(metadata)

        items.sort(key=lambda item: item.get("ingested_at") or "", reverse=True)

        lines = [
            f"- {item.get('title', 'Untitled')} | {item.get('source_url', '')} | {item.get('file_path', '')}"
            for item in items[:limit]
        ]

        return "\n".join(lines) or "No saved articles found."

    return Tool(
        name="list_recent_articles",
        description="List recent saved Markdown articles. Input is an optional numeric limit.",
        func=_run,
    )


def get_article_sources_tool(config: AppConfig, logger):
    """Create a tool for finding source URLs for matching articles."""
    def _normalize(text: str) -> str:
        """Normalize text for loose article-title matching."""
        return " ".join(text.lower().replace("-", " ").split())

    def _query_tokens(text: str) -> set[str]:
        """Extract meaningful query tokens for source matching."""
        stopwords = {
            "berikan",
            "source",
            "sources",
            "url",
            "tentang",
            "untuk",
            "dari",
            "artikel",
            "reference",
            "references",
            "sumber",
            "give",
            "me",
            "about",
            "the",
        }

        return {
            token
            for token in _normalize(text).split()
            if len(token) > 2 and token not in stopwords
        }

    def _run(query: str) -> str:
        """Return matching source URLs from metadata or retrieved documents."""
        query_norm = _normalize(query)
        tokens = _query_tokens(query)

        matched_sources: list[str] = []
        seen: set[str] = set()

        for file_path in list_markdown_files(config.output_dir):
            try:
                document = load_markdown_file(file_path)
                metadata = document.metadata
            except Exception:
                metadata = parse_frontmatter(Path(file_path).read_text(encoding="utf-8"))
                metadata["file_path"] = file_path

            title = _normalize(metadata.get("title", ""))
            source = metadata.get("source_url")

            if not source:
                continue

            title_matches_query = title and title in query_norm
            token_match_count = sum(1 for token in tokens if token in title)
            has_strong_token_match = bool(tokens) and token_match_count >= min(2, len(tokens))

            if source not in seen and (title_matches_query or has_strong_token_match):
                seen.add(source)
                matched_sources.append(source)

        if matched_sources:
            return "\n".join(matched_sources)

        documents = retrieve_documents(query, config, logger)

        for document in documents:
            source = document.metadata.get("source_url")
            if source and source not in seen:
                seen.add(source)
                matched_sources.append(source)

        return "\n".join(matched_sources[:3]) or "No matching sources found."

    return Tool(
        name="get_article_sources",
        description="Return source URLs from matching local articles.",
        func=_run,
    )


def tavily_web_search_tool(config: AppConfig, logger):
    """Create a tool for explicit Tavily web searches."""
    def _run(query: str) -> str:
        """Return formatted Tavily search results for a query."""
        results = search_tavily(query, config, logger)
        lines = [
            f"- {result.title}: {result.url}\n  {result.content}"
            for result in results
        ]
        return "\n".join(lines) or "No Tavily results available."

    return Tool(
        name="tavily_web_search",
        description="Search the web using Tavily when latest web information is explicitly requested.",
        func=_run,
    )


def ingest_external_sources_tool(config: AppConfig, logger):
    """Create a tool for saving Tavily results as local Markdown sources."""
    def _run(query: str) -> str:
        """Search Tavily and save new external results as Markdown files."""
        limit = _parse_limit_from_query(query)
        results = search_tavily(query, config, logger)

        if not results:
            return "No Tavily results available to save."

        existing_urls = _existing_source_urls(config)
        today = datetime.now(timezone.utc).date().isoformat()
        output_dir = Path(config.output_dir) / today
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files: list[str] = []
        skipped_urls: list[str] = []

        for result in results[:limit]:
            if result.url in existing_urls:
                skipped_urls.append(result.url)
                continue

            slug = _slugify(result.title)
            file_path = output_dir / f"{slug}.md"

            counter = 2
            while file_path.exists():
                file_path = output_dir / f"{slug}-{counter}.md"
                counter += 1

            ingested_at = datetime.now(timezone.utc).isoformat()

            markdown = "\n".join(
                [
                    "---",
                    f'title: "{_escape_frontmatter(result.title)}"',
                    f'source_url: "{_escape_frontmatter(result.url)}"',
                    'source_type: "tavily"',
                    f'ingested_at: "{ingested_at}"',
                    "---",
                    "",
                    f"# {result.title}",
                    "",
                    f"Source: {result.url}",
                    "",
                    "## Content",
                    "",
                    result.content.strip() or "No content summary available.",
                    "",
                    "## Links",
                    "",
                    f"- {result.url}",
                    "",
                ]
            )

            file_path.write_text(markdown, encoding="utf-8")
            existing_urls.add(result.url)
            saved_files.append(str(file_path))

            logger.info(
                "External source saved",
                extra={"event": "external_source.saved"},
            )

        if not saved_files and skipped_urls:
            return "No new external sources saved. All matching sources already exist locally."

        lines = ["Saved external sources:"]
        lines.extend(f"- {file_path}" for file_path in saved_files)

        if skipped_urls:
            lines.append("")
            lines.append("Skipped existing sources:")
            lines.extend(f"- {url}" for url in skipped_urls)

        return "\n".join(lines)

    return Tool(
        name="ingest_external_sources",
        description=(
            "Search external web sources using Tavily and save selected results "
            "as local Markdown files. Use only when the user explicitly asks to save "
            "external sources locally."
        ),
        func=_run,
    )


def create_agent_tools(config: AppConfig, logger) -> list:
    """Create the full set of LangChain tools used by the agent."""
    return [
        search_ai_articles_tool(config, logger),
        list_recent_articles_tool(config),
        get_article_sources_tool(config, logger),
        tavily_web_search_tool(config, logger),
        ingest_external_sources_tool(config, logger),
    ]
