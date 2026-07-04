import requests

from src.exceptions import AppError


def fetch_html(url: str, timeout: int, user_agent: str, logger) -> str:
    """Fetch HTML content from a URL using the configured request settings."""
    logger.info("Fetching article", extra={"event": "article.fetch.start", "url": url})
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": user_agent},
            allow_redirects=True,
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            logger.warning(
                "Fetched content is not HTML",
                extra={"event": "article.fetch.non_html", "url": url},
            )

        html = response.text
        if not html:
            raise AppError("FETCH_FAILED", "Empty HTML response")

        logger.info("Fetched article", extra={"event": "article.fetch.done", "url": url})
        return html
    except requests.Timeout as error:
        raise AppError("FETCH_FAILED", "Request timeout", error) from error
    except requests.RequestException as error:
        raise AppError("FETCH_FAILED", "Request failed", error) from error
