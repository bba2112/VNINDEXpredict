import time
from datetime import datetime
from typing import Optional, Tuple

import feedparser

# RSS sources to poll. Add or remove as needed.
FEEDS = [
    "https://vnexpress.net/rss/tin-moi-nhat.rss"
    # "https://cafef.vn/du-lieu/rss.chn",
    # "https://thesaigontimes.vn/feed/",
]

# Initial ticker text (will be overwritten on first new title)
ticker_text = (
    "Tin nhanh: VNINDEX biến động mạnh trong phiên | VN30 giữ nhịp | "
    "Thanh khoản cải thiện | Cập nhật từ nguồn API sẽ thay thế nội dung này"
)

last_title = None
last_link = None
last_updated_at = None


def _entry_timestamp(entry) -> float:
    # Prefer published, fall back to updated; return 0 if missing.
    ts = entry.get("published_parsed") or entry.get("updated_parsed")
    if not ts:
        return 0.0
    return time.mktime(ts)


def fetch_latest_title() -> Tuple[Optional[str], Optional[str]]:
    latest_entry = None
    latest_ts = 0.0

    for url in FEEDS:
        feed = feedparser.parse(url)
        if not feed.entries:
            continue
        for entry in feed.entries:
            ts = _entry_timestamp(entry)
            if ts > latest_ts:
                latest_ts = ts
                latest_entry = entry

    if not latest_entry:
        return None, None

    return latest_entry.get("title")


def write_ticker_text(text: str) -> None:
    # UI can read this file directly.
    with open("ticker_text.txt", "w", encoding="utf-8") as f:
        f.write(text)


while True:
    try:
        title = fetch_latest_title()

        if title and (title != last_title):
            last_title = title
            last_updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            ticker_text = f"Tin nhanh: {last_title}"

            write_ticker_text(ticker_text)

        print(ticker_text) 

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(600)  # 10 minutes