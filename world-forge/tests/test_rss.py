from app.world.rss import parse_feed

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Journal</title>
    <item>
      <title>Premier titre</title>
      <description>Premier résumé.</description>
      <pubDate>Wed, 01 Jul 2026 08:00:00 +0200</pubDate>
    </item>
    <item>
      <title>Deuxième titre</title>
    </item>
  </channel>
</rss>"""

ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Blog</title>
  <entry>
    <title>Billet Atom</title>
    <summary>Résumé Atom.</summary>
    <updated>2026-07-01T08:00:00Z</updated>
  </entry>
</feed>"""


def test_parse_rss2():
    items = parse_feed(RSS, feed_name="Journal")

    assert [item.title for item in items] == ["Premier titre", "Deuxième titre"]
    assert items[0].summary == "Premier résumé."
    assert items[0].published is not None and items[0].published.year == 2026
    assert items[1].published is None  # pubDate absent : pas d'erreur


def test_parse_atom():
    items = parse_feed(ATOM, feed_name="Blog")

    assert items[0].title == "Billet Atom"
    assert items[0].summary == "Résumé Atom."
    assert items[0].published is not None


def test_max_items_limite_le_nombre():
    assert len(parse_feed(RSS, feed_name="Journal", max_items=1)) == 1
