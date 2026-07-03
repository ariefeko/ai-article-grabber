from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from src.collector.extractor import (
    extract_article,
    extract_content,
    extract_images,
    extract_links,
    extract_published_at,
    extract_title,
    extract_videos,
)
from src.exceptions import AppError
from src.types import CandidateArticle

FIXTURE = Path(__file__).parent / "fixtures" / "sample_article.html"


def _soup():
    return BeautifulSoup(FIXTURE.read_text(encoding="utf-8"), "lxml")


def test_extract_title_uses_candidate_first():
    assert extract_title(_soup(), CandidateArticle("Candidate", "https://example.com/a", "feed")) == "Candidate"


def test_extract_published_at_uses_candidate_first():
    article = CandidateArticle("Title", "https://example.com/a", "feed", published_at="2026-07-04T01:00:00")
    assert extract_published_at(_soup(), article) == "2026-07-04T01:00:00"


def test_extract_content_returns_text():
    html = FIXTURE.read_text(encoding="utf-8")
    assert "retrieval augmented generation" in extract_content(html, _soup())


def test_extract_images_absolute_urls():
    urls = [item.url for item in extract_images(_soup(), "https://example.com/article")]
    assert "https://example.com/images/main.jpg" in urls
    assert "https://cdn.example.com/secondary.jpg" in urls


def test_extract_links_absolute_and_skips_invalid():
    urls = [item.url for item in extract_links(_soup(), "https://example.com/article")]
    assert "https://example.com/reference" in urls
    assert "https://example.com/relative-report" in urls
    assert not any(url.startswith("mailto:") for url in urls)


def test_extract_videos_urls():
    urls = [item.url for item in extract_videos(_soup(), "https://example.com/article")]
    assert "https://www.youtube.com/embed/example" in urls
    assert "https://example.com/video/sample.mp4" in urls


def test_extract_article_returns_article():
    html = FIXTURE.read_text(encoding="utf-8")
    candidate = CandidateArticle("Candidate", "https://example.com/article", "feed")
    article = extract_article(html, candidate, "2026-07-04T12:00:00+07:00")
    assert article.title == "Candidate"
    assert article.images


def test_extract_article_empty_raises():
    candidate = CandidateArticle("Candidate", "https://example.com/article", "feed")
    with pytest.raises(AppError):
        extract_article("<html><body>short</body></html>", candidate, "2026-07-04T12:00:00+07:00")
