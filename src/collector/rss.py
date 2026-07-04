from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser

from src.collector.date import parse_article_date
from src.collector.url import normalize_url
from src.types import CandidateArticle


def is_ai_related_article(article: CandidateArticle, keywords: list[str]) -> bool:
    """Check whether an article title or summary matches AI keywords."""
    haystack = f"{article.title} {article.summary}".lower()
    return any(keyword.lower() in haystack for keyword in keywords)


def collect_candidate_articles(
    feed_urls: list[str],
    keywords: list[str],
    logger,
) -> list[CandidateArticle]:
    """Collect AI-related candidate articles from configured RSS feeds."""
    logger.info("Collecting RSS articles", extra={"event": "rss.collect.start"})
    articles: list[CandidateArticle] = []

    for feed_url in feed_urls:
        try:
            feed = feedparser.parse(feed_url)
            if getattr(feed, "bozo", False):
                logger.warning(
                    "RSS feed warning",
                    extra={
                        "event": "rss.feed.warning",
                        "url": feed_url,
                        "error_message": str(getattr(feed, "bozo_exception", "")),
                    },
                )

            for entry in feed.entries:
                title = getattr(entry, "title", "") or ""
                url = getattr(entry, "link", "") or ""
                summary = (
                    getattr(entry, "summary", "")
                    or getattr(entry, "description", "")
                    or ""
                )
                published_at = (
                    getattr(entry, "published", None)
                    or getattr(entry, "updated", None)
                )
                if not url:
                    continue

                article = CandidateArticle(
                    title=title,
                    url=normalize_url(url),
                    summary=summary,
                    published_at=parse_article_date(published_at),
                    source_feed_url=feed_url,
                )
                if is_ai_related_article(article, keywords):
                    articles.append(article)
        except Exception as error:
            logger.error(
                "RSS feed failed",
                extra={
                    "event": "rss.feed.failed",
                    "url": feed_url,
                    "error_message": str(error),
                },
            )

    articles = remove_duplicate_articles(articles)
    articles = sort_articles_by_newest(articles)
    logger.info(
        "Collected RSS articles",
        extra={"event": "rss.collect.done", "count": len(articles)},
    )
    return articles


def _date_sort_key(article: CandidateArticle) -> datetime:
    """Return a datetime key for sorting articles by publication date."""
    if not article.published_at:
        return datetime.min
    try:
        return datetime.fromisoformat(article.published_at.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        try:
            return parsedate_to_datetime(article.published_at).replace(tzinfo=None)
        except (TypeError, ValueError):
            return datetime.min


def sort_articles_by_newest(articles: list[CandidateArticle]) -> list[CandidateArticle]:
    """Sort candidate articles from newest to oldest."""
    return sorted(articles, key=_date_sort_key, reverse=True)


def remove_duplicate_articles(articles: list[CandidateArticle]) -> list[CandidateArticle]:
    """Remove duplicate candidate articles by normalized URL."""
    seen: set[str] = set()
    unique_articles: list[CandidateArticle] = []
    for article in articles:
        normalized = normalize_url(article.url)
        if normalized in seen:
            continue
        seen.add(normalized)
        article.url = normalized
        unique_articles.append(article)
    return unique_articles
