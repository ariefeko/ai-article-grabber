from bs4 import BeautifulSoup
from readability import Document as ReadabilityDocument

from src.collector.date import parse_article_date
from src.collector.url import (
    absolute_url,
    dedupe_media_items,
    get_domain,
    is_valid_http_url,
)
from src.exceptions import AppError
from src.types import CandidateArticle, ExtractedArticle, MediaItem

REMOVABLE_SELECTORS = ["script", "style", "noscript", "nav", "footer", "header", "aside", "form", "iframe"]
VIDEO_DOMAINS = ("youtube.com", "youtu.be", "vimeo.com", "player.vimeo.com", "dailymotion.com", "tiktok.com")


def extract_article(
    html: str,
    candidate: CandidateArticle,
    ingested_at: str,
) -> ExtractedArticle:
    """Extract structured article data and media from raw HTML."""
    try:
        soup = BeautifulSoup(html, "lxml")
        title = extract_title(soup, candidate)
        content = extract_content(html, soup)
        if len(content.strip()) < 80:
            raise AppError("ARTICLE_EMPTY", "Extracted article content is empty")

        return ExtractedArticle(
            title=title,
            source_url=candidate.url,
            source_domain=get_domain(candidate.url),
            ingested_at=ingested_at,
            content=content,
            published_at=extract_published_at(soup, candidate),
            images=extract_images(soup, candidate.url),
            links=extract_links(soup, candidate.url),
            videos=extract_videos(soup, candidate.url),
        )
    except AppError:
        raise
    except Exception as error:
        raise AppError("EXTRACT_FAILED", "Failed to extract article", error) from error


def extract_title(soup: BeautifulSoup, candidate: CandidateArticle) -> str:
    """Choose the best available article title from feed and page metadata."""
    if candidate.title.strip():
        return candidate.title.strip()
    meta_title = soup.select_one('meta[property="og:title"]')
    if meta_title and meta_title.get("content"):
        return meta_title["content"].strip()
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(" ", strip=True)
    title = soup.find("title")
    if title and title.get_text(strip=True):
        return title.get_text(" ", strip=True)
    return "Untitled Article"


def extract_published_at(soup: BeautifulSoup, candidate: CandidateArticle) -> str | None:
    """Extract and normalize an article publication timestamp."""
    if candidate.published_at:
        return parse_article_date(candidate.published_at)
    selectors = [
        'meta[property="article:published_time"]',
        'meta[name="publish-date"]',
        'meta[name="date"]',
    ]
    for selector in selectors:
        meta = soup.select_one(selector)
        if meta and meta.get("content"):
            return parse_article_date(meta["content"])
    time_tag = soup.select_one("time[datetime]")
    if time_tag and time_tag.get("datetime"):
        return parse_article_date(time_tag["datetime"])
    return None


def _clean_soup(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove non-content elements from a BeautifulSoup document."""
    for tag in soup.select(",".join(REMOVABLE_SELECTORS)):
        tag.decompose()
    return soup


def extract_content(html: str, soup: BeautifulSoup) -> str:
    """Extract readable article text from HTML with fallback selectors."""
    try:
        summary_html = ReadabilityDocument(html).summary()
        summary_soup = _clean_soup(BeautifulSoup(summary_html, "lxml"))
        text = summary_soup.get_text("\n", strip=True)
        if text:
            return text
    except Exception:
        pass

    clean_soup = _clean_soup(BeautifulSoup(str(soup), "lxml"))
    for selector in ["article", "main", "body"]:
        element = clean_soup.find(selector)
        if element:
            text = element.get_text("\n", strip=True)
            if text:
                return text
    return clean_soup.get_text("\n", strip=True)


def _image_url_from_srcset(srcset: str) -> str:
    """Return the first image URL from an HTML srcset attribute."""
    first = srcset.split(",")[0].strip()
    return first.split(" ")[0]


def extract_images(soup: BeautifulSoup, base_url: str) -> list[MediaItem]:
    """Collect image URLs from image tags and social metadata."""
    items: list[MediaItem] = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if not src and img.get("srcset"):
            src = _image_url_from_srcset(img["srcset"])
        if not src:
            continue
        url = absolute_url(base_url, src)
        if is_valid_http_url(url):
            items.append(MediaItem(url=url, label=img.get("alt", "").strip() or "Article image"))

    for selector in ['meta[property="og:image"]', 'meta[name="twitter:image"]']:
        meta = soup.select_one(selector)
        if meta and meta.get("content"):
            url = absolute_url(base_url, meta["content"])
            if is_valid_http_url(url):
                items.append(MediaItem(url=url, label="Article image"))
    return dedupe_media_items(items)


def extract_links(soup: BeautifulSoup, base_url: str) -> list[MediaItem]:
    """Collect valid HTTP links from anchor tags."""
    items: list[MediaItem] = []
    for link in soup.find_all("a"):
        href = (link.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        url = absolute_url(base_url, href)
        if not is_valid_http_url(url):
            continue
        label = link.get_text(" ", strip=True) or url
        items.append(MediaItem(url=url, label=label[:120]))
    return dedupe_media_items(items)


def extract_videos(soup: BeautifulSoup, base_url: str) -> list[MediaItem]:
    """Collect embedded video and media URLs from the article page."""
    items: list[MediaItem] = []
    selectors = ["iframe[src]", "video[src]", "video source[src]"]
    for selector in selectors:
        for tag in soup.select(selector):
            src = tag.get("src")
            if not src:
                continue
            url = absolute_url(base_url, src)
            if is_valid_http_url(url):
                label = "Embedded video" if any(domain in url for domain in VIDEO_DOMAINS) else "Embedded media"
                items.append(MediaItem(url=url, label=label))

    for selector in [
        'meta[property="og:video"]',
        'meta[property="og:video:url"]',
        'meta[property="og:video:secure_url"]',
    ]:
        meta = soup.select_one(selector)
        if meta and meta.get("content"):
            url = absolute_url(base_url, meta["content"])
            if is_valid_http_url(url):
                items.append(MediaItem(url=url, label="Embedded video"))
    return dedupe_media_items(items)
