from tavily import TavilyClient

from src.types import AppConfig, TavilySearchResult


def is_tavily_enabled(config: AppConfig) -> bool:
    """Return whether Tavily search is configured."""
    return bool(config.tavily_api_key)


def search_tavily(
    query: str,
    config: AppConfig,
    logger,
) -> list[TavilySearchResult]:
    """Search Tavily and return normalized search results."""
    if not is_tavily_enabled(config):
        logger.warning("Tavily disabled", extra={"event": "tavily.search.disabled"})
        return []

    logger.info("Searching Tavily", extra={"event": "tavily.search.start"})
    try:
        client = TavilyClient(api_key=config.tavily_api_key)
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=config.tavily_max_results,
        )
        results = [
            TavilySearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
            )
            for item in response.get("results", [])
        ]
        logger.info(
            "Tavily search done",
            extra={"event": "tavily.search.done", "count": len(results)},
        )
        return results
    except Exception as error:
        logger.error(
            "Tavily search failed",
            extra={
                "event": "tavily.search.failed",
                "error_code": "TAVILY_FAILED",
                "error_message": str(error),
            },
        )
        return []


def format_tavily_results_for_context(
    results: list[TavilySearchResult],
) -> str:
    """Format Tavily results as context for an LLM prompt."""
    return "\n\n".join(
        [
            "\n".join(
                [
                    f"Title: {result.title}",
                    f"URL: {result.url}",
                    f"Content: {result.content}",
                ]
            )
            for result in results
        ]
    )
