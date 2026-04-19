"""Fetch Taiwan stock-specific news via Google News RSS."""

import asyncio
import re
from urllib.parse import quote
from datetime import datetime
from typing import Optional

import httpx
import feedparser
from loguru import logger
from cachetools import TTLCache


# 15-minute cache per stock
news_cache: TTLCache = TTLCache(maxsize=500, ttl=900)

# Full browser-like headers to avoid Google 503 blocks on datacenter IPs
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "DNT": "1",
}


def _clean_title(title: str) -> str:
    """Remove source suffix Google News adds (e.g. ' - 經濟日報')."""
    title = re.sub(r"\s*-\s*[^-]+$", "", title).strip()
    return title


def _extract_source(entry) -> str:
    """Extract source name from a feedparser entry."""
    if hasattr(entry, "source") and hasattr(entry.source, "title"):
        return entry.source.title
    title = entry.get("title", "")
    m = re.search(r"\s*-\s*([^-]+)$", title)
    if m:
        return m.group(1).strip()
    return ""


def _format_published(published_str: str) -> str:
    """Format published date to short Chinese form."""
    if not published_str:
        return ""
    try:
        dt = datetime.strptime(published_str, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.strftime("%m/%d %H:%M")
    except Exception:
        return published_str[:16]


class NewsService:
    """Fetches stock-specific news from Google News RSS."""

    async def get_stock_news(
        self,
        stock_id: str,
        stock_name: str = "",
        limit: int = 5,
    ) -> list[dict]:
        """
        Get the latest news for a specific stock.

        Query pattern: "{stock_id} {stock_name}" (e.g. "2330 台積電")
        - Uses Google News RSS (no API key required)
        - httpx async client with browser-like headers
        - 15-minute cache per stock
        - Returns up to `limit` items
        """
        cache_key = f"news:{stock_id}:{limit}"
        if cache_key in news_cache:
            return news_cache[cache_key]

        query_parts = [stock_id]
        if stock_name and stock_name != stock_id:
            query_parts.append(stock_name)
        query = " ".join(query_parts)

        url = (
            f"https://news.google.com/rss/search?"
            f"q={quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        )

        try:
            async with httpx.AsyncClient(
                headers=_HEADERS,
                follow_redirects=True,
                timeout=15.0,
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)

            if not feed.entries:
                logger.debug(f"No news found for {stock_id} ({stock_name})")
                news_cache[cache_key] = []
                return []

            items = []
            for entry in feed.entries[:limit]:
                title = _clean_title(entry.get("title", ""))
                if not title:
                    continue
                items.append({
                    "title": title,
                    "source": _extract_source(entry),
                    "published": _format_published(entry.get("published", "")),
                    "link": entry.get("link", ""),
                })

            news_cache[cache_key] = items
            return items

        except Exception as e:
            logger.warning(f"Failed to fetch news for {stock_id}: {e}")
            return []
