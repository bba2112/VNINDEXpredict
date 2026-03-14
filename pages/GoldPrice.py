import altair as alt
import pandas as pd
import streamlit as st
from datetime import date, timedelta
from vnstock.explorer.misc.gold_price import sjc_gold_price

st.set_page_config(page_title="Giá vàng hôm nay - Greatfut", layout="wide")

def _nav_button(label: str, page_path: str) -> None:
    if hasattr(st, "switch_page"):
        if st.button(label, use_container_width=True):
            st.switch_page(page_path)
        return
    if hasattr(st, "page_link"):
        st.page_link(page_path, label=label, use_container_width=True)
        return
    st.info("Streamlit không hỗ trợ chuyển trang trong phiên bản này.")

a1, a2, a3 = st.columns(3)
with a1:
    _nav_button("Bảng giá thị trường", "./dashboard.py")
with a2:
    _nav_button("Danh sách các quỹ", "pages/Quymo.py")
with a3:
    _nav_button("VNData", "pages/VNIndex.py")

st.title("Bảng giá vàng SJC")

@st.cache_data(ttl=3600)
def load_gold_price() -> pd.DataFrame:
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    snapshots: list[pd.DataFrame] = []
    for day in pd.date_range(start=start_date, end=end_date, freq="7D"):
        raw = sjc_gold_price(date=day.strftime("%Y-%m-%d"))
        if isinstance(raw, pd.DataFrame) and not raw.empty:
            snapshots.append(raw.copy())

    if not snapshots:
        return pd.DataFrame()

    hist = pd.concat(snapshots, ignore_index=True)
    hist["date"] = pd.to_datetime(hist["date"], errors="coerce")

    hist = (
        hist.groupby("date", as_index=False)[["buy_price", "sell_price"]]
        .mean()
        .sort_values("date")
        .reset_index(drop=True)
    )
    return hist


def _pick_column(columns: pd.Index, candidates: list[str]) -> str | None:
    normalized = {
        col: str(col).strip().lower().replace(" ", "").replace("_", "")
        for col in columns
    }
    for candidate in candidates:
        key = candidate.strip().lower().replace(" ", "").replace("_", "")
        for col, norm in normalized.items():
            if norm == key:
                return col
    return None


def _to_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(r"[^\d,.\-]", "", regex=True)
        .str.replace(",", "", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


try:
    with st.spinner("Đang tải dữ liệu giá vàng ..."):
        df = load_gold_price()
except Exception as exc:
    st.error(f"Không tải được dữ liệu giá vàng: {exc}")
    st.stop()

if df.empty:
    st.warning("Không có dữ liệu giá vàng hiện tại")
else:
    x_col = _pick_column(df.columns, ["date", "ngay", "time", "timestamp"])
    if x_col:
        x_values = pd.to_datetime(df[x_col], errors="coerce")
        x_is_datetime = x_values.notna().any()
        x_title = str(x_col)
        x_data = x_values if x_is_datetime else df[x_col].astype(str)
    else:
        x_is_datetime = False
        x_title = "Index"
        x_data = df.index + 1

    series_candidates = [
        "buy_price",
        "sell_price",
        "buy",
        "sell",
        "mua",
        "ban",
        "gia_mua",
        "gia_ban",
        "gia",
        "price",
    ]

    y_cols: list[str] = []
    for key in series_candidates:
        col = _pick_column(df.columns, [key])
        if col and col not in y_cols:
            y_cols.append(col)

    if not y_cols:
        for col in df.columns:
            numeric = _to_numeric(df[col])
            if numeric.notna().sum() > 0:
                y_cols.append(col)
            if len(y_cols) >= 3:
                break

    chart_df = pd.DataFrame({"x": x_data})
    for col in y_cols:
        chart_df[col] = _to_numeric(df[col])

    chart_long = (
        chart_df.melt(id_vars="x", var_name="Series", value_name="Price")
        .dropna(subset=["Price"])
        .reset_index(drop=True)
    )

    if chart_long.empty:
        st.info("Không tìm thấy cột giá hợp lệ để vẽ biểu đồ")
    else:
        x_encoding = (
            alt.X("x:T", title=x_title)
            if x_is_datetime
            else alt.X("x:N", title=x_title)
        )
        chart = (
            alt.Chart(chart_long)
            .mark_line(point=True)
            .encode(
                x=x_encoding,
                y=alt.Y("Price:Q", title="Giá"),
                color=alt.Color("Series:N", title="Loại giá"),
                tooltip=[
                    alt.Tooltip("x:T" if x_is_datetime else "x:N", title=x_title),
                    alt.Tooltip("Series:N", title="Loại"),
                    alt.Tooltip("Price:Q", title="Giá", format=",.0f"),
                ],
            )
            .properties(height=420)
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)

    st.caption("Dữ liệu 3 năm gần nhất, lấy mẫu mỗi 7 ngày")

    with st.expander("Dữ liệu raw", expanded=False):
        st.dataframe(df, use_container_width=True)

    st.caption(f"Số dòng: {len(df):,}")
