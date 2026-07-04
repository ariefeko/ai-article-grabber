from src.collector.date import now_iso, today_date_string
from src.collector.extractor import extract_article
from src.collector.fetcher import fetch_html
from src.collector.filesystem import (
    append_ingested_url,
    ensure_directories,
    generate_unique_markdown_path,
    get_output_directory,
    read_ingested_urls,
    save_text_file,
)
from src.collector.markdown import render_markdown
from src.collector.rss import collect_candidate_articles
from src.collector.url import normalize_url
from src.config import load_config
from src.constants import KEYWORDS, RSS_FEEDS
from src.exceptions import AppError
from src.logger import setup_logger
from src.rag.indexer import index_markdown_articles
from src.types import AppConfig


def run_ingestion_pipeline(config: AppConfig, logger) -> tuple[int, int, int]:
    """Collect, save, and index new AI articles."""
    ensure_directories(config)
    ingested_urls = read_ingested_urls(config.ingested_urls_file)
    candidates = collect_candidate_articles(RSS_FEEDS, KEYWORDS, logger)

    new_candidates = []
    for candidate in candidates:
        normalized_url = normalize_url(candidate.url)
        if normalized_url in ingested_urls:
            logger.info(
                "Skipping duplicate article",
                extra={"event": "article.skip.duplicate", "url": normalized_url},
            )
            continue
        new_candidates.append(candidate)
        if len(new_candidates) >= config.max_articles:
            break

    if not new_candidates:
        logger.info("No new articles selected", extra={"event": "article.none"})
    else:
        logger.info(
            "Selected articles",
            extra={"event": "article.selected", "count": len(new_candidates)},
        )

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
                logger,
            )
            article = extract_article(
                html=html,
                candidate=candidate,
                ingested_at=now_iso(config.timezone),
            )
            markdown = render_markdown(article)
            file_path = generate_unique_markdown_path(output_directory, article.title)
            save_text_file(file_path, markdown)
            append_ingested_url(config.ingested_urls_file, normalize_url(candidate.url))
            saved_count += 1
            logger.info(
                "Saved Markdown article",
                extra={
                    "event": "article.markdown.saved",
                    "url": candidate.url,
                    "file_path": file_path,
                },
            )
        except AppError as error:
            failed_count += 1
            logger.error(
                "Article failed",
                extra={
                    "event": "article.failed",
                    "url": candidate.url,
                    "error_code": error.code,
                    "error_message": error.message,
                },
            )
        except Exception as error:
            failed_count += 1
            logger.exception(
                "Unexpected article failure",
                extra={
                    "event": "article.unexpected_failed",
                    "url": candidate.url,
                    "error_message": str(error),
                },
            )

    try:
        indexed_count = index_markdown_articles(config, logger)
    except AppError as error:
        indexed_count = 0
        logger.error(
            "RAG indexing failed",
            extra={
                "event": "rag.index.failed",
                "error_code": error.code,
                "error_message": error.message,
            },
        )

    return saved_count, failed_count, indexed_count


def main() -> None:
    """Run the article ingestion pipeline as a script."""
    config = load_config()
    logger = setup_logger(config)
    logger.info("Application started", extra={"event": "app.start"})
    saved_count, failed_count, indexed_count = run_ingestion_pipeline(config, logger)
    logger.info(
        "Application done",
        extra={
            "event": "app.done",
            "count": saved_count,
            "saved_count": saved_count,
            "failed_count": failed_count,
            "indexed_count": indexed_count,
        },
    )


if __name__ == "__main__":
    main()
