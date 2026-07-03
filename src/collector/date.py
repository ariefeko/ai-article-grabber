from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo


def now_iso(timezone: str) -> str:
    return datetime.now(ZoneInfo(timezone)).isoformat(timespec="seconds")


def today_date_string(timezone: str) -> str:
    return datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d")


def parse_article_date(date_value: str | None) -> str | None:
    if not date_value:
        return None
    try:
        return parsedate_to_datetime(date_value).isoformat()
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(date_value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return date_value
