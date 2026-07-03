from src.collector.markdown import render_markdown
from src.types import ExtractedArticle, MediaItem


def _article(images=None, links=None, videos=None):
    return ExtractedArticle(
        title="Sample AI Article",
        source_url="https://example.com/article",
        source_domain="example.com",
        published_at="2026-07-04T09:30:00",
        ingested_at="2026-07-04T12:00:00+07:00",
        content="Article content goes here.",
        images=images or [],
        links=links or [],
        videos=videos or [],
    )


def test_render_markdown_includes_frontmatter_title_source_content():
    markdown = render_markdown(_article())
    assert 'title: "Sample AI Article"' in markdown
    assert "# Sample AI Article" in markdown
    assert "https://example.com/article" in markdown
    assert "Article content goes here." in markdown


def test_render_markdown_images_links_videos_html():
    markdown = render_markdown(
        _article(
            images=[MediaItem("https://example.com/image.jpg", "Image")],
            links=[MediaItem("https://example.com/link", "Link")],
            videos=[MediaItem("https://example.com/video", "Video")],
        )
    )
    assert 'target="_blank"' in markdown
    assert 'rel="noopener noreferrer"' in markdown
    assert "<img src=" in markdown


def test_render_markdown_empty_media_fallbacks():
    markdown = render_markdown(_article())
    assert "No images found." in markdown
    assert "No links found." in markdown
    assert "No videos or embedded media found." in markdown
