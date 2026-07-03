from pathlib import Path

from langchain_core.tools import Tool

from src.collector.filesystem import list_markdown_files
from src.fallback.tavily_search import search_tavily
from src.rag.chain import ask_with_fallback
from src.rag.loader import load_markdown_file, parse_frontmatter
from src.rag.retriever import retrieve_documents
from src.types import AppConfig


def search_ai_articles_tool(config: AppConfig, logger):
    def _run(question: str) -> str:
        result = ask_with_fallback(question, config, logger)
        sources = "\n".join(result.sources)
        return f"{result.answer}\n\nSources:\n{sources}" if sources else result.answer

    return Tool(
        name="search_ai_articles",
        description="Search local AI article knowledge base using RAG and Tavily fallback if needed.",
        func=_run,
    )


def list_recent_articles_tool(config: AppConfig):
    def _run(limit_text: str = "5") -> str:
        try:
            limit = int(limit_text.strip() or "5")
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
    def _run(query: str) -> str:
        documents = retrieve_documents(query, config, logger)
        sources = []
        seen = set()
        for document in documents:
            source = document.metadata.get("source_url")
            if source and source not in seen:
                seen.add(source)
                sources.append(source)
        return "\n".join(sources) or "No matching sources found."

    return Tool(
        name="get_article_sources",
        description="Return source URLs from matching local articles.",
        func=_run,
    )


def tavily_web_search_tool(config: AppConfig, logger):
    def _run(query: str) -> str:
        results = search_tavily(query, config, logger)
        lines = [f"- {result.title}: {result.url}\n  {result.content}" for result in results]
        return "\n".join(lines) or "No Tavily results available."

    return Tool(
        name="tavily_web_search",
        description="Search the web using Tavily when latest web information is explicitly requested.",
        func=_run,
    )


def create_agent_tools(config: AppConfig, logger) -> list:
    return [
        search_ai_articles_tool(config, logger),
        list_recent_articles_tool(config),
        get_article_sources_tool(config, logger),
        tavily_web_search_tool(config, logger),
    ]
