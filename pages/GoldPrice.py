import altair as alt
import pandas as pd
import streamlit as st
from datetime import date, timedelta
from vnstock.explorer.misc.gold_price import sjc_gold_price
from vnstock.explorer.misc.exchange_rate import *
from datetime import date
import os
try:
    from gemini_ai import GeminiAI
except Exception:
    GeminiAI = None
from common import load_css, render_topbar

def today_str() -> str:
    return date.today().isoformat()


st.set_page_config(page_title="Giá vàng hôm nay - Greatfut", layout="wide")
load_css()
day = timedelta(days=0)
cr = vcb_exchange_rate(date = today_str())

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

TICKER_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ticker_text.txt")

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
    os.path.dirname(os.path.dirname(__file__)),
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
    extra_class="topbar--gold",
)

### Giá vàng ###

def _nav_button(label: str, page_path: str) -> None:
    if hasattr(st, "switch_page"):
        if st.button(label, use_container_width=True):
            st.switch_page(page_path)
        return
    if hasattr(st, "page_link"):
        st.page_link(page_path, label=label, use_container_width=True)
        return
    st.info("Streamlit không hỗ trợ chuyển trang trong phiên bản này.")

a1, a2, a3,a4 = st.columns(4)
with a1:
    _nav_button("Bảng giá thị trường", "./dashboard.py")
with a2:
    _nav_button("Danh sách các quỹ", "pages/Quymo.py")
with a3:
    _nav_button("VNData", "pages/VNIndex.py")
with a4:
    _nav_button("Toàn cảnh thị trường", "pages/Toancanh_thitruong.py")

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



### GEMINI ###

def get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()

@st.cache_resource
def get_gemini_client(api_key: str):
    if GeminiAI is None or not api_key:
        return None
    return GeminiAI(api_key=api_key, gemini_model="gemini-2.5-flash")

def build_gold_ai_context(df: pd.DataFrame) -> str:
    if df.empty:
        return "Khong co du lieu gia vang."

    # Chuẩn hoá cột ngày
    if "date" in df.columns:
        dates = pd.to_datetime(df["date"], errors="coerce")
    else:
        dates = pd.Series([None] * len(df))

    # Cột giá
    buy = df.get("buy_price")
    sell = df.get("sell_price")

    def _to_float(series):
        return pd.to_numeric(series, errors="coerce") if series is not None else None

    buy = _to_float(buy)
    sell = _to_float(sell)

    first_buy = float(buy.dropna().iloc[0]) if buy is not None and buy.dropna().any() else None
    last_buy = float(buy.dropna().iloc[-1]) if buy is not None and buy.dropna().any() else None
    first_sell = float(sell.dropna().iloc[0]) if sell is not None and sell.dropna().any() else None
    last_sell = float(sell.dropna().iloc[-1]) if sell is not None and sell.dropna().any() else None

    start_dt = dates.min()
    end_dt = dates.max()

    def pct(a, b):
        return ((b - a) / a * 100) if a and b else None

    return (
        f"Loai: Gia vang SJC\n"
        f"Khoang thoi gian: {start_dt} den {end_dt}\n"
        f"So diem du lieu: {len(df)}\n"
        f"Gia mua dau ky: {first_buy}\n"
        f"Gia mua cuoi ky: {last_buy}\n"
        f"Bien dong mua: {pct(first_buy, last_buy)}%\n"
        f"Gia ban dau ky: {first_sell}\n"
        f"Gia ban cuoi ky: {last_sell}\n"
        f"Bien dong ban: {pct(first_sell, last_sell)}%\n"
    )

api_key = get_gemini_api_key()
with st.popover("💬", help="Trợ lí AI", use_container_width=False):
    st.markdown("### Trợ lí AI")
    user_question = st.text_area(
        "Nhập câu hỏi",
        value="",
        height=100,
        key="ai_user_question",
    )

    if st.button("Gửi", use_container_width=True, key="ai_submit_btn"):
        if GeminiAI is None:
            st.error("Không import được gemini_ai trong môi trường chạy Streamlit.")
        elif not api_key:
            st.error("Thiếu GEMINI_API_KEY. Hãy đặt trong biến môi trường hoặc st.secrets.")
        elif not user_question.strip():
            st.warning("Vui lòng nhập nội dung câu hỏi.")
        else:
            try:
                client = get_gemini_client(api_key)
                context = build_gold_ai_context(df)
                prompt = (
                    "Ban la tro li phan tich gia vang Viet Nam. "
                    "Tra loi ngan gon theo muc: Xu huong, Moc quan trong, Rui ro, Goi y hanh dong.\n\n"
                    f"Du lieu gia vang:\n{context}\n"
                    f"Yeu cau nguoi dung: {user_question.strip()}"
                )
                with st.spinner("Đang phân tích..."):
                    response = client.model.generate_content(prompt)
                st.session_state["ai_answer_text"] = getattr(response, "text", "").strip() or "AI không trả về nội dung."
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


    with st.expander("Dữ liệu giá vàng", expanded=False):
        st.dataframe(df, use_container_width=True)

    st.caption(f"Số dòng: {len(df):,}")

### Giá ngoại tệ ###
st.title ("Tỷ giá ngoại tệ")
st.dataframe(cr)
st.title("Tính chênh lệch tỷ giá từ đồng VND")

with st.form("Chuyển đổi tiền tệ"):
    st.subheader("Tính chênh lệch tỷ giá từ đồng VND")
    amount = st.number_input("Số tiền (VND)", min_value=0, value=0, step=100000)
    target_currency = st.selectbox("Chọn loại ngoại tệ", options=cr["currency_code"].tolist())
    
    submit = st.form_submit_button("Tính toán")
    if submit:
        rate_row = cr[cr["currency_code"] == target_currency]
        if not rate_row.empty:
            exchange_rate_raw = rate_row["sell"].iloc[0]
            exchange_rate = float(str(exchange_rate_raw).replace(",", "").strip())

            converted_amount = amount / exchange_rate
            st.success(f"{amount:,.0f} VND tương đương với {converted_amount:,.2f} {target_currency} (tỷ giá: {exchange_rate:,.2f} VND/{target_currency})")
        else:
            st.error("Không tìm thấy tỷ giá cho loại ngoại tệ đã chọn.")

