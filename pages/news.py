import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(page_title="Tin Tuc", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
HTML_PATH = BASE_DIR / "news_site" / "dist" / "index.html"

st.title("Tin Tuc")

if not HTML_PATH.exists():
    st.warning(
        "Chua co index.html. Hay chay: `python news_site\\news.py` de tao trang."
    )
else:
    html = HTML_PATH.read_text(encoding="utf-8")
    components.html(html, height=1200, scrolling=True)
