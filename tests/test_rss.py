from src.collector.rss import (
    is_ai_related_article,
    remove_duplicate_articles,
    sort_articles_by_newest,
)
from src.types import CandidateArticle


def test_is_ai_related_article_title():
    article = CandidateArticle("AI breakthrough", "https://e.com/a", "feed")
    assert is_ai_related_article(article, ["ai"])


def test_is_ai_related_article_summary():
    article = CandidateArticle("News", "https://e.com/a", "feed", summary="About machine learning")
    assert is_ai_related_article(article, ["machine learning"])


def test_is_ai_related_article_false():
    article = CandidateArticle("Garden", "https://e.com/a", "feed", summary="Plants")
    assert not is_ai_related_article(article, ["ai"])


def test_remove_duplicate_articles():
    articles = [
        CandidateArticle("A", "https://e.com/a#x", "feed"),
        CandidateArticle("B", "https://e.com/a", "feed"),
    ]
    assert len(remove_duplicate_articles(articles)) == 1


def test_sort_articles_by_newest():
    articles = [
        CandidateArticle("Old", "https://e.com/old", "feed", published_at="2026-07-03T00:00:00"),
        CandidateArticle("New", "https://e.com/new", "feed", published_at="2026-07-04T00:00:00"),
    ]
    assert sort_articles_by_newest(articles)[0].title == "New"
