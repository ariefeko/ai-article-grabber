from html import escape

from src.types import ExtractedArticle


def escape_yaml_value(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()


def html_link(url: str, label: str) -> str:
    safe_url = escape(url, quote=True)
    safe_label = escape(label or url)
    return f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">{safe_label}</a>'


def html_image(url: str, alt: str) -> str:
    safe_url = escape(url, quote=True)
    safe_alt = escape(alt or "Article image", quote=True)
    return (
        f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">\n'
        f'  <img src="{safe_url}" alt="{safe_alt}" />\n'
        "</a>"
    )


def _render_media_section(title: str, lines: list[str], fallback: str) -> str:
    body = "\n\n".join(lines) if lines else fallback
    return f"## {title}\n\n{body}"


def render_markdown(article: ExtractedArticle) -> str:
    images = [html_image(item.url, item.label) for item in article.images]
    links = [f"- {html_link(item.url, item.label)}" for item in article.links]
    videos = [f"- {html_link(item.url, item.label)}" for item in article.videos]

    published = article.published_at or ""

    return "\n".join(
        [
            "---",
            f'title: "{escape_yaml_value(article.title)}"',
            f'source_url: "{escape_yaml_value(article.source_url)}"',
            f'source_domain: "{escape_yaml_value(article.source_domain)}"',
            f'published_at: "{escape_yaml_value(article.published_at)}"',
            f'ingested_at: "{escape_yaml_value(article.ingested_at)}"',
            "---",
            "",
            f"# {article.title}",
            "",
            f"Source: {html_link(article.source_url, article.source_url)}  ",
            f"Published: {published or 'Unknown'}  ",
            f"Ingested: {article.ingested_at}  ",
            "",
            "---",
            "",
            "## Content",
            "",
            article.content.strip(),
            "",
            "---",
            "",
            _render_media_section("Images", images, "No images found."),
            "",
            "---",
            "",
            _render_media_section("Links", links, "No links found."),
            "",
            "---",
            "",
            _render_media_section("Videos / Embedded Media", videos, "No videos or embedded media found."),
            "",
        ]
    )
