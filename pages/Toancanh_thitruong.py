import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from vnstock import Quote

st.set_page_config(page_title="Toàn cảnh thị trường", layout="wide")

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
INDUSTRY_FILE = os.path.join(ROOT_DIR, "industries.json")
REFRESH_SECONDS = 60


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
st.caption("Heatmap theo ngành từ industries.json.")

data = load_industries(INDUSTRY_FILE)
meta = data.get("meta", {})
industries = data.get("industries", [])

left, right = st.columns([7, 3], gap="large")
with right:
    st.subheader("Thiết lập")
    source = st.selectbox("Nguồn dữ liệu", ["VCI", "TCBS", "KBS"], index=0)
    max_per_industry = st.slider("Giới hạn số mã mỗi ngành", 5, 50, 15, step=1)
    st.caption("Tự động cập nhật mỗi 60 giây (chỉ heatmap).")

def render_heatmap() -> None:
    if not industries:
        st.warning("Chưa có danh sách ngành. Hãy cập nhật industries.json.")
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
    st.caption("Màu sắc theo % thay đổi trong phiên, kích thước theo khối lượng.")

    symbols = tuple(sorted({row["symbol"] for row in all_rows}))
    snapshot_df = fetch_realtime_snapshots(symbols, source)
    merged = pd.DataFrame(all_rows).merge(snapshot_df, on="symbol", how="left")

    if merged.empty:
        st.warning("Không lấy được dữ liệu realtime.")
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
        hover_data={
            "symbol": True,
            "pct_change": ":.2f",
            "volume": ":,.0f",
            "last_price": ":.2f",
        },
    )
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Chi tiết dữ liệu")
    st.dataframe(
        merged.sort_values(["industry", "pct_change"], ascending=[True, False]),
        use_container_width=True,
        hide_index=True,
    )


with left:
    if hasattr(st, "fragment"):
        @st.fragment(run_every=REFRESH_SECONDS)
        def _heatmap_fragment() -> None:
            render_heatmap()

        _heatmap_fragment()
    else:
        render_heatmap()
