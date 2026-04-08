import datetime as dt
import re
import sys
from pathlib import Path

try:
    import feedparser
except Exception:
    print("Missing dependency: feedparser")
    print("Install with: pip install feedparser")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
TEMPLATE_PATH = BASE_DIR / "template.html"
OUT_DIR = BASE_DIR / "dist"
OUT_PATH = OUT_DIR / "index.html"

SITE_TITLE = "Tin Nhanh"
SITE_SUBTITLE = "Trang tin tu RSS (HTML tinh)"

FEEDS = [
    {
        "name": "Hacker News",
        "url": "https://news.ycombinator.com/rss",
    },
    {
        "name": "BBC World",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
    },
]

MAX_ITEMS = 18


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def format_time(struct_time) -> str:
    try:
        return dt.datetime(*struct_time[:6]).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


def collect_items():
    items = []
    for feed in FEEDS:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries:
            summary = strip_html(getattr(entry, "summary", ""))
            if len(summary) > 160:
                summary = summary[:157] + "..."
            pub = format_time(getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None))
            items.append(
                {
                    "title": getattr(entry, "title", "(no title)"),
                    "link": getattr(entry, "link", "#"),
                    "summary": summary or "Khong co tom tat.",
                    "source": feed["name"],
                    "time": pub,
                }
            )
    return items


def render_card(item: dict) -> str:
    time_html = f"<span>{item['time']}</span>" if item["time"] else ""
    return (
        '<article class="card">'
        f'<div class="source">{item["source"]}</div>'
        f'<h2>{item["title"]}</h2>'
        f'<p>{item["summary"]}</p>'
        f'<div><a href="{item["link"]}" target="_blank" rel="noopener">Doc tiep</a> {time_html}</div>'
        "</article>"
    )


def main():
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    items = collect_items()
    items = items[:MAX_ITEMS]
    cards = "\n".join(render_card(i) for i in items) or "<p>Khong co tin nao.</p>"

    updated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    html = (
        template.replace("{{TITLE}}", SITE_TITLE)
        .replace("{{SUBTITLE}}", SITE_SUBTITLE)
        .replace("{{UPDATED_AT}}", updated_at)
        .replace("{{CARDS}}", cards)
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
