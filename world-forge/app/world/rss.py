"""Analyse de flux RSS 2.0 et Atom en stdlib pur (pas de feedparser : dépendance
évitée, les deux dialectes couvrent les flux courants)."""

import contextlib
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

from app.schemas import FeedItem

_ATOM = "{http://www.w3.org/2005/Atom}"


def parse_feed(xml_text: str, feed_name: str, max_items: int = 5) -> list[FeedItem]:
    root = ElementTree.fromstring(xml_text)
    if root.tag == f"{_ATOM}feed":
        entries = root.findall(f"{_ATOM}entry")
        return [_atom_item(entry, feed_name) for entry in entries[:max_items]]
    items = root.findall("./channel/item")
    return [_rss_item(item, feed_name) for item in items[:max_items]]


def _text(element: ElementTree.Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _rss_item(item: ElementTree.Element, feed_name: str) -> FeedItem:
    published: datetime | None = None
    pub_date = _text(item.find("pubDate"))
    if pub_date:
        with contextlib.suppress(ValueError, TypeError):
            published = parsedate_to_datetime(pub_date)
    return FeedItem(
        feed=feed_name,
        title=_text(item.find("title")),
        summary=_text(item.find("description")),
        published=published,
    )


def _atom_item(entry: ElementTree.Element, feed_name: str) -> FeedItem:
    published: datetime | None = None
    stamp = _text(entry.find(f"{_ATOM}published")) or _text(entry.find(f"{_ATOM}updated"))
    if stamp:
        with contextlib.suppress(ValueError):
            published = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    return FeedItem(
        feed=feed_name,
        title=_text(entry.find(f"{_ATOM}title")),
        summary=_text(entry.find(f"{_ATOM}summary")),
        published=published,
    )
