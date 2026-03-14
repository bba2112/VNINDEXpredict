import pandas as pd
import streamlit as st
from vnstock import Fund


st.set_page_config(page_title="Quỹ mở Việt Nam - Greatfut", layout="wide")
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
    _nav_button("Giá vàng", "pages/GoldPrice.py")
with a3:
    _nav_button("VNData", "pages/VNIndex.py")
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