import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from vnstock import Quote

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
from constants import index_options
import json

from vnstock import Company, Listing, Quote
try:
    from streamlit_elements import elements, mui, html
except Exception:
    elements = None
    mui = None
    html = None

import os
try:
    from gemini_ai import GeminiAI
except Exception:
    GeminiAI = None
from constants import (
    index_options,
    quote_symbols,
    group_symbols,
    GROUP_ELIGIBLE,
    INDEX_TO_QUOTE,
)
from common import load_css, render_topbar
st.set_page_config(page_title="Toàn cảnh thị trường", layout="wide")


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
INDUSTRY_FILE = os.path.join(ROOT_DIR, "industries.json")
REFRESH_SECONDS = 600
load_css()

### BAR ###
# Auto-refresh page to pick up ticker file changes.
st.components.v1.html(
    "<script>setTimeout(() => window.location.reload(), 3600000);</script>",
    height=0,
)

# Placeholder ticker text (used if no file-driven content yet)
_ticker_default = (
    "Tin nhanh: VNINDEX biến động mạnh trong phiên | VN30 giữ nhịp | "
    "Thanh khoản cải thiện | Cập nhật từ nguồn API sẽ thay thế nội dung này"
)

TICKER_FILE = os.path.join(ROOT_DIR, "ticker_text.txt")

def load_ticker_text(default_text: str) -> str:
    try:
        if os.path.exists(TICKER_FILE):
            with open(TICKER_FILE, "r", encoding="utf-8", errors="replace") as f:
                text = f.read().strip()
                if text:
                    return text
    except Exception:
        pass
    return default_text

ticker_text = load_ticker_text(_ticker_default)

logo_path = os.path.join(
    ROOT_DIR,
    "image",
    "Gemini_Generated_Image_uvz9l1uvz9l1uvz9.png",
)
render_topbar(
    ticker_text=ticker_text,
    ticker_text_en=(
        "Breaking: VNINDEX volatile | VN30 steady | Liquidity improving | "
        "API feed will replace this"
    ),
    logo_path=logo_path,
    clock_timezone="Asia/Ho_Chi_Minh",
    extra_class="topbar--dashboard",
)

### NAVIGATION ### 
def _nav_button(label: str, page_path: str) -> None:
    if hasattr(st, "switch_page"):
        if st.button(label, use_container_width=True):
            st.switch_page(page_path)
        return
    if hasattr(st, "page_link"):
        st.page_link(page_path, label=label, use_container_width=True)
        return
    st.info("Streamlit không hỗ trợ chuyển trang trong phiên bản này.")

a1, a2, a3, a4 = st.columns(4)
with a1:
    _nav_button("Bảng giá thị trường", "./dashboard.py")
with a2:
    _nav_button("Danh sách các quỹ", "pages/Quymo.py")
with a3:
    _nav_button("VNData", "pages/VNIndex.py")
with a4:
    _nav_button("Giá vàng", "pages/GoldPrice.py")


### GEMINI AI ###

def get_gemini_api_key() -> str:
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    secret_key = ""
    try:
        secret_key = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        secret_key = ""
    return env_key or secret_key

@st.cache_resource
def get_gemini_client(api_key: str):
    if GeminiAI is None or not api_key:
        return None
    return GeminiAI(api_key=api_key, gemini_model="gemini-2.5-flash")

def build_market_context(merged_df: pd.DataFrame) -> str:
    if merged_df is None or merged_df.empty:
        return "Không có dữ liệu realtime để tổng hợp."

    df = merged_df.copy()
    for col in ["pct_change", "last_price", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    total = int(df["symbol"].nunique()) if "symbol" in df.columns else len(df)
    adv = int((df["pct_change"] > 0).sum()) if "pct_change" in df.columns else 0
    dec = int((df["pct_change"] < 0).sum()) if "pct_change" in df.columns else 0
    flat = max(total - adv - dec, 0)

    def _top(df_in: pd.DataFrame, col: str, n: int, ascending: bool):
        if col not in df_in.columns:
            return ""
        tmp = df_in.dropna(subset=[col])
        if tmp.empty:
            return ""
        tmp = tmp.sort_values(col, ascending=ascending).head(n)
        lines = []
        for _, row in tmp.iterrows():
            sym = row.get("symbol", "")
            val = row.get(col, None)
            if col == "pct_change" and val is not None:
                lines.append(f"{sym}: {val:.2f}%")
            elif col == "volume" and val is not None:
                lines.append(f"{sym}: {val:,.0f}")
            elif col == "last_price" and val is not None:
                lines.append(f"{sym}: {val:,.2f}")
        return ", ".join(lines)

    top_gainers = _top(df, "pct_change", 5, ascending=False)
    top_losers = _top(df, "pct_change", 5, ascending=True)
    top_volume = _top(df, "volume", 5, ascending=False)

    industry_summary = ""
    if "industry" in df.columns and "pct_change" in df.columns:
        ind_df = df.dropna(subset=["industry"]).groupby("industry")["pct_change"].mean().sort_values(ascending=False)
        if not ind_df.empty:
            top_ind = ind_df.head(3)
            bottom_ind = ind_df.tail(3)
            industry_summary = (
                "Ngành tăng tốt: "
                + ", ".join([f"{k}: {v:.2f}%" for k, v in top_ind.items()])
                + "\\n"
                + "Ngành giảm mạnh: "
                + ", ".join([f"{k}: {v:.2f}%" for k, v in bottom_ind.items()])
            )

    return (
        f"Tổng số mã: {total}\\n"
        f"Tăng: {adv} | Giảm: {dec} | Đứng giá: {flat}\\n"
        f"Top tăng: {top_gainers or 'N/A'}\\n"
        f"Top giảm: {top_losers or 'N/A'}\\n"
        f"Top khối lượng: {top_volume or 'N/A'}\\n"
        + (industry_summary if industry_summary else "")
    )


def load_industries(path: str) -> dict:
    if not os.path.exists(path):
        return {"meta": {}, "industries": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"meta": {}, "industries": []}
        if "industries" not in data or not isinstance(data["industries"], list):
            data["industries"] = []
        return data
    except Exception:
        return {"meta": {}, "industries": []}


def _pick_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


@st.cache_data(ttl=55, show_spinner=False)
def fetch_symbol_intraday(symbol: str, source: str) -> pd.DataFrame:
    quote = Quote(symbol=symbol, source=source)
    return quote.intraday(page_size=120)


@st.cache_data(ttl=55, show_spinner=False)
def fetch_realtime_snapshots(symbols: tuple[str, ...], source: str) -> pd.DataFrame:
    rows = []
    for symbol in symbols:
        symbol = str(symbol).strip().upper()
        if not symbol:
            continue
        try:
            intraday = fetch_symbol_intraday(symbol, source)
            if intraday is None or intraday.empty:
                rows.append(
                    {"symbol": symbol, "last_price": None, "pct_change": None, "volume": None}
                )
                continue

            price_col = _pick_col(intraday, ["price", "close", "last_price", "match_price"])
            vol_col = _pick_col(intraday, ["volume", "match_volume", "vol", "total_volume"])
            time_col = _pick_col(intraday, ["time", "timestamp", "trade_time"])

            df = intraday.copy()
            if time_col:
                df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
                df = df.dropna(subset=[time_col]).sort_values(time_col)

            if price_col is None:
                rows.append(
                    {"symbol": symbol, "last_price": None, "pct_change": None, "volume": None}
                )
                continue

            df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
            first_price = df[price_col].dropna().iloc[0] if not df[price_col].dropna().empty else None
            last_price = df[price_col].dropna().iloc[-1] if not df[price_col].dropna().empty else None

            volume = None
            if vol_col and vol_col in df.columns:
                df[vol_col] = pd.to_numeric(df[vol_col], errors="coerce")
                volume = df[vol_col].sum(skipna=True)

            pct_change = None
            if first_price and last_price:
                pct_change = (last_price - first_price) / first_price * 100

            rows.append(
                {
                    "symbol": symbol,
                    "last_price": last_price,
                    "pct_change": pct_change,
                    "volume": volume,
                }
            )
        except Exception:
            rows.append({"symbol": symbol, "last_price": None, "pct_change": None, "volume": None})

    return pd.DataFrame(rows)


st.title("Toàn cảnh thị trường")

data = load_industries(INDUSTRY_FILE)
meta = data.get("meta", {})
industries = data.get("industries", [])

left, right = st.columns([7, 3], gap="large")
with right:
    st.subheader("Thị trường hôm nay")
    source = st.selectbox("Nguồn dữ liệu", ["VCI", "TCBS", "KBS"], index=0)
    max_per_industry = st.slider("Giới hạn số lượng mã mỗi ngành", 5, 50, 15, step=1)
    st.caption("Tự động cập nhật dữ liệu mỗi 60 giây (chuyển đổi heatmap).")


with st.popover("💬", help="Trợ lí AI", use_container_width=False):
    st.markdown("### Trợ lí AI")
    user_question = st.text_area(
        "Nhập câu hỏi",
        value="",
        height=100,
        key="ai_user_question",
    )

    if st.button("Gửi", use_container_width=True, key="ai_submit_btn"):
        api_key = get_gemini_api_key()
        if GeminiAI is None:
            st.error("Không import được gemini_ai trong môi trường chạy Streamlit.")
        elif not api_key:
            st.error("Thiếu GEMINI_API_KEY. Hãy đặt trong biến môi trường hoặc st.secrets.")
        elif not user_question.strip():
            st.warning("Vui lòng nhập nội dung câu hỏi.")
        else:
            try:
                # Build realtime context on demand.
                all_rows = []
                for item in industries:
                    name = item.get("name", "")
                    symbols = item.get("symbols", [])[:max_per_industry]
                    for symbol in symbols:
                        all_rows.append({"industry": name, "symbol": symbol})

                symbols = tuple(sorted({row["symbol"] for row in all_rows}))
                snapshot_df = fetch_realtime_snapshots(symbols, source)
                merged_df = pd.DataFrame(all_rows).merge(snapshot_df, on="symbol", how="left")
                context = build_market_context(merged_df)

                client = get_gemini_client(api_key)
                if client is None:
                    st.error("Không khởi tạo được Gemini client.")
                else:
                    prompt = (
                        "Bạn là trợ lí phân tích chứng khoán Việt Nam. "
                        "Trả lời ngắn gọn theo mục: Xu hướng, Mốc quan trọng, Rủi ro, Gợi ý hành động.\\n\\n"
                        f"Dữ liệu thị trường (tổng hợp realtime):\\n{context}\\n"
                        f"Yêu cầu người dùng: {user_question.strip()}"
                    )
                    with st.spinner("Đang phân tích..."):
                        response = client.model.generate_content(prompt)
                    st.session_state["ai_answer_text"] = (
                        getattr(response, "text", "").strip() or "AI không trả về nội dung."
                    )
            except Exception as exc:
                err_text = str(exc)
                if "reported as leaked" in err_text or "403" in err_text:
                    st.error(
                        "Gemini API key đã bị thu hồi hoặc không hợp lệ (403). "
                        "Hãy tạo key mới và cập nhật GEMINI_API_KEY trong st.secrets hoặc biến môi trường."
                    )
                else:
                    st.error(f"Lỗi gọi Gemini: {exc}")

    if st.session_state.get("ai_answer_text"):
        st.markdown("#### Kết quả AI")
        st.markdown(st.session_state["ai_answer_text"])

def render_heatmap() -> None:
    if not industries:
        st.warning("Chưa có danh sách ngành trong file industries.json.")
        return

    all_rows = []
    for item in industries:
        name = item.get("name", "")
        symbols = item.get("symbols", [])[:max_per_industry]
        for symbol in symbols:
            all_rows.append({"industry": name, "symbol": symbol})

    if not all_rows:
        st.warning("Danh sách ngành rỗng.")
        return

    st.subheader("Tổng quan theo ngành")
    st.caption("Mẫu số liệu theo % thay đổi trong phiên, kích thước theo khối lượng giao dịch.")

    symbols = tuple(sorted({row["symbol"] for row in all_rows}))
    snapshot_df = fetch_realtime_snapshots(symbols, source)
    merged = pd.DataFrame(all_rows).merge(snapshot_df, on="symbol", how="left")

    if merged.empty:
        st.warning("Không có dữ liệu realtime.")
        return

    merged["volume"] = merged["volume"].fillna(0)
    merged["size"] = merged["volume"].replace(0, 1)

    fig = px.treemap(
        merged,
        path=["industry", "symbol"],
        values="size",
        color="pct_change",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        labels={
            "industry": "Ngành",
            "symbol": "Mã",
            "pct_change": "% thay đổi",
            "volume": "Khối lượng",
            "last_price": "Giá cuối cùng",
            "size": "Khối lượng",
        },
        hover_data={
            "symbol": True,
            "pct_change": ":.2f",
            "volume": ":,.0f",
            "last_price": ":.2f",
        },
    )
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig, use_container_width=True)



with left:
    if hasattr(st, "fragment"):
        @st.fragment(run_every=REFRESH_SECONDS)
        def _heatmap_fragment() -> None:
            render_heatmap()

        _heatmap_fragment()
    else:
        render_heatmap()
