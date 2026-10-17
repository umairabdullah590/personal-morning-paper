"""Step 1: pull today's stories from RSS feeds into the articles table."""
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from html import unescape
from time import mktime

import feedparser
import requests

from core import config, db

HEADERS = {
    "User-Agent": "MorningPaper/1.0 (personal daily newspaper; github.com/umairabdullah590/personal-morning-paper)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}


def _plain(text):
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _published(entry):
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                return datetime.utcfromtimestamp(mktime(parsed)).isoformat(timespec="seconds")
            except (OverflowError, ValueError, OSError):
                continue
    return config.utcnow().isoformat(timespec="seconds")


def _image(entry):
    media = entry.get("media_content") or entry.get("media_thumbnail") or []
    if media and isinstance(media, list) and media[0].get("url"):
        return media[0]["url"]
    for enc in entry.get("enclosures") or []:
        typ = (enc.get("type") or "")
        href = enc.get("href") or enc.get("url")
        if href and typ.startswith("image"):
            return href
    html = entry.get("summary") or entry.get("description") or ""
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
    return match.group(1) if match else None


def _entry_url(entry):
    link = entry.get("link") or ""
    if link:
        return link
    for alt in entry.get("links") or []:
        if alt.get("href"):
            return alt["href"]
    return ""


def fetch_feed(feed):
    """Return (new_count, ok: bool)."""
    try:
        resp = requests.get(feed["url"], headers=HEADERS, timeout=20)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except Exception:
        return 0, False

    new = 0
    for entry in parsed.entries[: config.PER_FEED_LIMIT]:
        url = _entry_url(entry)
        title = _plain(entry.get("title") or "")
        if not url or not title:
            continue
        snippet = _plain(entry.get("summary") or entry.get("description") or "")[:800]
        if db.upsert_article({
            "url": url,
            "title": title,
            "source": feed["name"],
            "published": _published(entry),
            "snippet": snippet,
            "image": _image(entry),
            "hint_topic": feed.get("topic"),
        }):
            new += 1
    return new, True


def fetch_all():
    """Fetch every feed. Returns (new_articles, feeds_ok, feeds_failed)."""
    db.init_db()
    new = ok = failed = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_feed, feed): feed for feed in config.FEEDS}
        for fut in as_completed(futures):
            n, succeeded = fut.result()
            new += n
            if succeeded:
                ok += 1
            else:
                failed += 1
    return new, ok, failed
