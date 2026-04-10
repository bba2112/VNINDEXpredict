import pandas as pd
import streamlit as st
from vnstock import Fund
from dotenv import load_dotenv
load_dotenv()

import os
from common import load_css, render_topbar
import os
try:
    from gemini_ai import GeminiAI
except Exception:
    GeminiAI = None

st.set_page_config(page_title="Quỹ mở Việt Nam - Greatfut", layout="wide")
load_css()

### Đóng SIDEBAR ### 
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Topbar
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
    extra_class="topbar--quymo",
)
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
    _nav_button("Bảng giá thị trường", "pages/dashboard.py")
with a2:
    _nav_button("Giá vàng", "pages/GoldPrice.py")
with a3:
    _nav_button("VNData", "pages/VNIndex.py")
with a4:
    _nav_button("Toàn cảnh thị trường", "pages/Toancanh_thitruong.py")
st.title("Danh sách quỹ mở")


@st.cache_resource
def get_fund_client() -> Fund:
    return Fund()


@st.cache_data(ttl=3600, show_spinner=False)
def load_fund_listing() -> pd.DataFrame:
    return get_fund_client().listing()


@st.cache_data(ttl=3600, show_spinner=False)
def load_top_holding(symbol: str) -> pd.DataFrame:
    return get_fund_client().details.top_holding(symbol)


def format_value(value, suffix: str = "") -> str:
    if pd.isna(value):
        return "-"
    if isinstance(value, (int, float)):
        return f"{value:,.2f}{suffix}"
    return f"{value}{suffix}"


def format_percent(value) -> str:
    return format_value(value, "%")


def render_metric(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div style="padding:10px 12px;border:1px solid #e5e7eb;border-radius:12px;background:#fafafa;">
            <div style="font-size:12px;color:#6b7280;">{label}</div>
            <div style="font-size:16px;font-weight:600;color:#111827;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


try:
    df = load_fund_listing()
except Exception as exc:
    st.error(f"Khong tai duoc danh sach quy: {exc}")
    st.stop()

if df.empty:
    st.warning("Khong co du lieu quy.")
    st.stop()

fund_type_options = ["Tất cả"] + sorted(df["fund_type"].dropna().astype(str).unique().tolist())

filter_left, filter_right = st.columns([1, 2])
with filter_left:
    selected_type = st.selectbox("Loại quỹ", fund_type_options)
with filter_right:
    keyword = st.text_input("Tìm theo mã quỹ / tên quỹ / công ty quản lý")

filtered_df = df.copy()

if selected_type != "Tất cả":
    filtered_df = filtered_df[filtered_df["fund_type"].astype(str) == selected_type]

if keyword.strip():
    term = keyword.strip().lower()
    mask = (
        filtered_df["short_name"].fillna("").astype(str).str.lower().str.contains(term)
        | filtered_df["name"].fillna("").astype(str).str.lower().str.contains(term)
        | filtered_df["fund_owner_name"].fillna("").astype(str).str.lower().str.contains(term)
    )
    filtered_df = filtered_df[mask]

st.caption(f"Số quỹ hiển thị: {len(filtered_df)} / {len(df)}")

for _, row in filtered_df.iterrows():
    symbol = str(row.get("short_name", "")).strip()

    with st.container(border=True):
        top_left, top_right = st.columns([3, 1])
        with top_left:
            st.subheader(symbol or "-")
            st.write(row.get("name", "-"))
            st.caption(
                f"Loại quỹ: {row.get('fund_type', '-')} | "
                f"Công ty quản lý: {row.get('fund_owner_name', '-')}"
            )
        with top_right:
            st.metric("NAV", format_value(row.get("nav")))
            st.caption(f"Cập nhật: {row.get('nav_update_at', '-')}")

        metric_cols = st.columns(5)
        with metric_cols[0]:
            render_metric("Phí quản lý", format_percent(row.get("management_fee")))
        with metric_cols[1]:
            render_metric("1 tháng", format_percent(row.get("nav_change_1m")))
        with metric_cols[2]:
            render_metric("12 tháng", format_percent(row.get("nav_change_12m")))
        with metric_cols[3]:
            render_metric("36 tháng", format_percent(row.get("nav_change_36m")))
        with metric_cols[4]:
            render_metric("36 tháng TB năm", format_percent(row.get("nav_change_36m_annualized")))

        extra_left, extra_right = st.columns(2)
        with extra_left:
            st.caption(
                f"Ngày thành lập: {row.get('inception_date', '-')} | "
                f"Mã quỹ: {row.get('fund_code', '-')}"
            )
        with extra_right:
            st.caption(
                f"Biến động từ ngày đầu: {format_percent(row.get('nav_change_inception'))} | "
                f"Biến động ngày trước: {format_percent(row.get('nav_change_previous'))}"
            )

        with st.expander(f"Xem top tỉ lệ nắm giữ của {symbol}", expanded=False):
            try:
                top_holding_df = load_top_holding(symbol)
            except Exception as exc:
                st.warning(f"Khong tai duoc top holding cho {symbol}: {exc}")
            else:
                if top_holding_df.empty:
                    st.info(f"Khong co du lieu top holding cho {symbol}.")
                else:
                    display_df = top_holding_df.copy()
                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                    if "net_asset_percent" in display_df.columns:
                        chart_df = display_df.dropna(subset=["net_asset_percent"]).copy()
                        if not chart_df.empty:
                            label_col = "stock_code" if "stock_code" in chart_df.columns else chart_df.columns[0]
                            chart_source = chart_df.set_index(label_col)["net_asset_percent"]
                            st.bar_chart(chart_source)

with st.expander("Xem dữ liệu bảng", expanded=False):
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

fund = Fund()
fund.details.industry_holding('BMFF')

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

def build_fund_context(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "Không có dữ liệu quỹ để tổng hợp."

    df = df.copy()
    for col in [
        "nav",
        "nav_change_1m",
        "nav_change_12m",
        "nav_change_36m",
        "nav_change_36m_annualized",
        "nav_change_inception",
        "nav_change_previous",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    total = len(df)
    type_counts = None
    if "fund_type" in df.columns:
        type_counts = (
            df["fund_type"]
            .fillna("Khác")
            .astype(str)
            .value_counts()
            .head(5)
            .to_dict()
        )

    def _top(df_in: pd.DataFrame, col: str, n: int, ascending: bool) -> str:
        if col not in df_in.columns:
            return ""
        tmp = df_in.dropna(subset=[col])
        if tmp.empty:
            return ""
        tmp = tmp.sort_values(col, ascending=ascending).head(n)
        lines = []
        for _, row in tmp.iterrows():
            sym = row.get("short_name", "") or row.get("fund_code", "")
            val = row.get(col, None)
            if val is None or pd.isna(val):
                continue
            if "nav_change" in col:
                lines.append(f"{sym}: {val:.2f}%")
            else:
                lines.append(f"{sym}: {val:,.2f}")
        return ", ".join(lines)

    top_nav = _top(df, "nav", 5, ascending=False)
    best_12m = _top(df, "nav_change_12m", 5, ascending=False)
    worst_12m = _top(df, "nav_change_12m", 5, ascending=True)

    type_summary = ""
    if type_counts:
        type_summary = "Phân bổ loại quỹ (top 5): " + ", ".join(
            [f"{k}: {v}" for k, v in type_counts.items()]
        )

    return (
        f"Tổng số quỹ: {total}\n"
        + (type_summary + "\n" if type_summary else "")
        + f"Top NAV: {top_nav or 'N/A'}\n"
        + f"Top hiệu suất 12M: {best_12m or 'N/A'}\n"
        + f"Bottom hiệu suất 12M: {worst_12m or 'N/A'}"
    )


with st.popover("💬", help="Trợ lí AI", use_container_width=False):
    st.markdown("### Trợ lí AI")
    user_question = st.text_area(
        "Nhập câu hỏi",
        value="",
        height=100,
        key="quymo_ai_user_question",
    )

    if st.button("Gửi", use_container_width=True, key="quymo_ai_submit_btn"):
        api_key = get_gemini_api_key()
        if GeminiAI is None:
            st.error("Không import được gemini_ai trong môi trường chạy Streamlit.")
        elif not api_key:
            st.error("Thiếu GEMINI_API_KEY. Hãy đặt trong biến môi trường hoặc st.secrets.")
        elif not user_question.strip():
            st.warning("Vui lòng nhập nội dung câu hỏi.")
        else:
            try:
                context = build_fund_context(filtered_df)

                client = get_gemini_client(api_key)
                if client is None:
                    st.error("Không khởi tạo được Gemini client.")
                else:
                    prompt = (
                        "Bạn là trợ lí phân tích quỹ đầu tư tại Việt Nam. "
                        "Trả lời ngắn gọn theo mục: Tổng quan, Điểm nổi bật, Rủi ro, Gợi ý hành động.\n\n"
                        f"Dữ liệu quỹ (tổng hợp):\n{context}\n"
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

if st.button("Đăng xuất"):
    st.session_state.pop("user", None)
    st.switch_page("C:\\Users\\kenda\\Desktop\\New folder (2)\\Greatfut.py")
