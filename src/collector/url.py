from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

from src.types import MediaItem


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    parsed = parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower())
    without_fragment = urldefrag(urlunparse(parsed)).url
    return without_fragment.rstrip("/")


def absolute_url(base_url: str, maybe_relative_url: str) -> str:
    return normalize_url(urljoin(base_url, maybe_relative_url.strip()))


def get_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def is_valid_http_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def dedupe_media_items(items: list[MediaItem]) -> list[MediaItem]:
    seen: set[str] = set()
    deduped: list[MediaItem] = []
    for item in items:
        normalized = normalize_url(item.url)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(MediaItem(url=normalized, label=item.label.strip() or normalized))
    return deduped
