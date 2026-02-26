import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from vnstock import Quote,Listing,Company

st.set_page_config(page_title="VNSTOCK", layout="wide")

st.title("VNSTOCK Dashboard")
st.subheader("Biểu đồ chỉ số")

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.8rem;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
        max-width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

index_options_vn =  ["HOSE", "VN30", "VNMidCap", "VNSmallCap", "VNAllShare", 
                     "VN100", "ETF", "HNX", "HNX30", "HNXCon", "HNXFin", "HNXLCap", 
                     "HNXMSCap", "HNXMan", "UPCOM", "FU_INDEX", "FU_BOND", "BOND", "CW"]
index_options_hnx = ["HNX", "HNX30", "HNXCon", "HNXFin", "HNXLCap", 
                     "HNXMSCap", "HNXMan"]
index_options_upcom = ["UpcomIndex","UPCOM"]
index_options_nganh = ["Dầu khí","Tài nguyên Cơ bản","Hàng & Dịch vụ Công nghiệp","Thực phẩm và đồ uống","Y tế","Truyền thông","Viễn thông","Ngân hàng","Bất động sản","Công nghệ Thông tin","Hóa chất","Xây dựng và Vật liệu","Ô tô và phụ tùng","Hàng cá nhân & Gia dụng",
                       "Bán lẻ","Du lịch và Giải trí","Điện,nước & xăng dầu khí đốt","Bảo hiểm","Dịch vụ tài chính"]


DEFAULT_CHOICE = "-- Chọn --"

if "selected_indexvn" not in st.session_state:
    st.session_state.selected_indexvn = DEFAULT_CHOICE
if "selected_indexhnx" not in st.session_state:
    st.session_state.selected_indexhnx = DEFAULT_CHOICE
if "selected_indexupcom" not in st.session_state:
    st.session_state.selected_indexupcom = DEFAULT_CHOICE


def on_change_vn():
    if st.session_state.selected_indexvn != DEFAULT_CHOICE:
        st.session_state.selected_indexhnx = DEFAULT_CHOICE
        st.session_state.selected_indexupcom = DEFAULT_CHOICE


def on_change_hnx():
    if st.session_state.selected_indexhnx != DEFAULT_CHOICE:
        st.session_state.selected_indexvn = DEFAULT_CHOICE
        st.session_state.selected_indexupcom = DEFAULT_CHOICE


def on_change_upcom():
    if st.session_state.selected_indexupcom != DEFAULT_CHOICE:
        st.session_state.selected_indexvn = DEFAULT_CHOICE
        st.session_state.selected_indexhnx = DEFAULT_CHOICE

c1, c2, c3, c9, c10 = st.columns([0.5, 0.5, 0.5, 0.4, 0.4])

with c1:
    st.selectbox(
        "Nhóm VN",
        [DEFAULT_CHOICE] + index_options_vn,
        key="selected_indexvn",
        on_change=on_change_vn,
    )

with c2:
    st.selectbox(
        "Nhóm HNX",
        [DEFAULT_CHOICE] + index_options_hnx,
        key="selected_indexhnx",
        on_change=on_change_hnx,
    )

with c3:
        st.selectbox(
            "Nhóm UPCOM",
            [DEFAULT_CHOICE] + index_options_upcom,
            key="selected_indexupcom",
            on_change=on_change_upcom,
        )

with c9:
    start_date = st.date_input("Từ ngày", pd.Timestamp.today().date() - pd.Timedelta(days=5))
with c10:
    end_date = st.date_input("Đến ngày", pd.Timestamp.today().date())

if start_date > end_date:
    st.error("Từ ngày không được lớn hơn đến ngày.")
    st.stop()

selected_indexvn = st.session_state.selected_indexvn
selected_indexhnx = st.session_state.selected_indexhnx
selected_indexupcom = st.session_state.selected_indexupcom


if selected_indexupcom != DEFAULT_CHOICE:
    selected_index = selected_indexupcom
elif selected_indexhnx != DEFAULT_CHOICE:
    selected_index = selected_indexhnx
elif selected_indexvn != DEFAULT_CHOICE:
    selected_index = selected_indexvn
else:
    st.warning("Vui lòng chọn chỉ số.")
    st.stop()

try:
    quote = Quote(symbol=selected_index, source="VCI")
    raw = quote.history(
        start=pd.to_datetime(start_date).strftime("%Y-%m-%d"),
        end=pd.to_datetime(end_date).strftime("%Y-%m-%d"),
        interval="1D",
    )
except Exception as exc:
    st.error(f"Không tải được dữ liệu {selected_index}: {exc}")
    st.stop()

if raw is None or raw.empty:
    st.warning(f"Không có dữ liệu cho {selected_index} trong khoảng ngày đã chọn.")
    st.stop()

df = raw[["time", "open", "high", "low", "close", "volume"]].copy()
df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df.dropna(subset=["time"]).sort_values("time")

for col in ["open", "high", "low", "close", "volume"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

left, right = st.columns([5, 1], gap="small")

with left:
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["time"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                increasing_line_color="#16a34a",
                decreasing_line_color="#dc2626",
                increasing_fillcolor="#16a34a",
                decreasing_fillcolor="#dc2626",
                name=selected_index,
            )
        ]
    )

    fig.update_layout(
        title=f"Biểu đồ giá của - {selected_index}",
        xaxis_title="Ngày",
        yaxis_title="Điểm",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        margin=dict(l=8, r=8, t=45, b=8),
        height=560,
    )

    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader(f"Danh sách công ty trong rổ {selected_index}")

@st.dialog("Chi tiết công ty", width="large")
def show_company_popup(symbol: str) -> None:
    st.write(f"### Mã: {symbol}")
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        ["Thông tin", "Cổ đông", "Ban lãnh đạo", "Công ty liên kết", "Tin tức", "Sự kiện", "Giá niêm yết"]
    )

    with tab1:
        try:
            company = Company(symbol=symbol, source="KBS")
            info_df = company.overview() if hasattr(company, "overview") else None
            if info_df is None:
                st.warning("Không có hàm thông tin phù hợp.")
            else:
                st.dataframe(info_df, use_container_width=True)
        except Exception as exc:
            st.warning(f"Không tải được thông tin {symbol}: {exc}")

    with tab2:
        try:
            company = Company(symbol=symbol, source="VCI")
            data = company.shareholders() if hasattr(company, "shareholders") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu cổ đông.")
        except Exception as exc:
            st.warning(f"Không tải được cổ đông {symbol}: {exc}")

    with tab3:
        try:
            company = Company(symbol=symbol, source="VCI")
            data = company.officers() if hasattr(company, "officers") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu ban lãnh đạo.")
        except Exception as exc:
            st.warning(f"Không tải được ban lãnh đạo {symbol}: {exc}")

    with tab4:
        try:
            company = Company(symbol=symbol, source="KBS")
            data = company.affiliate() if hasattr(company, "affiliate") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu công ty liên kết.")
        except Exception as exc:
            st.warning(f"Không tải được công ty liên kết {symbol}: {exc}")

    with tab5:
        try:
            company = Company(symbol=symbol, source="VCI")
            data = company.news() if hasattr(company, "news") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu tin tức.")
        except Exception as exc:
            st.warning(f"Không tải được tin tức {symbol}: {exc}")

    with tab6:
        try:
            company = Company(symbol=symbol, source="VCI")
            data = company.events() if hasattr(company, "events") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu sự kiện.")
        except Exception as exc:
            st.warning(f"Không tải được sự kiện {symbol}: {exc}")

    with tab7:
        try:
            q = Quote(symbol=symbol, source="VCI")
            price_hist_df = q.history(
                start=pd.to_datetime(start_date).strftime("%Y-%m-%d"),
                end=pd.to_datetime(end_date).strftime("%Y-%m-%d"),
                interval="1D",
            )
            st.dataframe(price_hist_df, use_container_width=True)
        except Exception as exc:
            st.warning(f"Không tải được giá niêm yết {symbol}: {exc}")

@st.cache_data(ttl=3600)
def get_group_symbols(group_name: str):
    listing = Listing(source="VCI")
    return listing.symbols_by_group(group_name)

GROUP_ELIGIBLE = {
    "VN30", "VN100", "VNDIAMOND", "VNFIN", "VNFINSELECT", "VNFINLEAD",
    "VNIND", "VNMID", "VNSML", "VNIT", "VNREAL", "VNCONS", "VNENE",
    "VNHEAL", "VNUTI", "VNMAT", "VNSI", "VNX50", "VNXALL", "VNALL", "VNCOND",
    "HNX30", "UpcomIndex"
}

show_df = pd.DataFrame()
event = None

if selected_index in GROUP_ELIGIBLE:
    try:
        basket_df = get_group_symbols(selected_index)

        if isinstance(basket_df, pd.Series):
            basket_df = basket_df.to_frame(name="symbol").reset_index(drop=True)
        elif not isinstance(basket_df, pd.DataFrame):
            basket_df = pd.DataFrame(basket_df)

    except Exception as exc:
        st.warning(f"Không lấy được danh sách rổ {selected_index}: {exc}")
        basket_df = pd.DataFrame()

    if basket_df.empty:
        st.info(f"Không có danh sách thành phần cho {selected_index}.")
    else:
        preferred_cols = ["symbol", "organ_name", "exchange", "icb_name2", "icb_name3"]
        show_cols = [c for c in preferred_cols if c in basket_df.columns]
        if not show_cols:
            show_cols = basket_df.columns.tolist()

        show_df = basket_df[show_cols].drop_duplicates()
        if "symbol" in show_df.columns:
            show_df = show_df.sort_values("symbol").reset_index(drop=True)

        event = st.dataframe(
            show_df,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
        )
        st.caption(f"Số mã trong rổ {selected_index}: {len(show_df)}")
else:
    st.info(f"{selected_index} không phải rổ có danh sách thành phần để hiển thị.")

if not show_df.empty and "symbol" in show_df.columns and event is not None:
    selected_rows = event.selection.rows
    if selected_rows:
        row_idx = selected_rows[0]
        selected_symbol = str(show_df.iloc[row_idx]["symbol"])
        show_company_popup(selected_symbol)
    else:
        st.info("Bấm vào 1 dòng để mở popup.")

#######################################
    st.title("Danh sách công ty theo ngành")

listing = Listing(source="VCI")

 #2) Toàn bộ mã + thông tin ngành
industry_df = listing.symbols_by_industries()

# Dùng list ngành bạn đã có sẵn
DEFAULT_CHOICE = "-- Chọn --"
selected_industry = st.selectbox(
    "Chọn nhóm ngành",
    [DEFAULT_CHOICE] + index_options_nganh,  # dùng biến của bạn
    index=0,
)

@st.dialog("Chi tiết công ty", width="large")
def show_company_popup(symbol: str) -> None:
    st.write(f"### Mã: {symbol}")
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        ["Thông tin", "Cổ đông", "Ban lãnh đạo", "Công ty liên kết", "Tin tức", "Sự kiện", "Giá niêm yết"]
    )

    with tab1:
        try:
            company = Company(symbol=symbol, source="KBS")
            info_df = company.overview() if hasattr(company, "overview") else None
            if info_df is None:
                st.warning("Không có hàm thông tin phù hợp.")
            else:
                st.dataframe(info_df, use_container_width=True)
        except Exception as exc:
            st.warning(f"Không tải được thông tin {symbol}: {exc}")

    with tab2:
        try:
            company = Company(symbol=symbol, source="VCI")
            data = company.shareholders() if hasattr(company, "shareholders") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu cổ đông.")
        except Exception as exc:
            st.warning(f"Không tải được cổ đông {symbol}: {exc}")

    with tab3:
        try:
            company = Company(symbol=symbol, source="VCI")
            data = company.officers() if hasattr(company, "officers") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu ban lãnh đạo.")
        except Exception as exc:
            st.warning(f"Không tải được ban lãnh đạo {symbol}: {exc}")

    with tab4:
        try:
            company = Company(symbol=symbol, source="KBS")
            data = company.affiliate() if hasattr(company, "affiliate") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu công ty liên kết.")
        except Exception as exc:
            st.warning(f"Không tải được công ty liên kết {symbol}: {exc}")

    with tab5:
        try:
            company = Company(symbol=symbol, source="VCI")
            data = company.news() if hasattr(company, "news") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu tin tức.")
        except Exception as exc:
            st.warning(f"Không tải được tin tức {symbol}: {exc}")

    with tab6:
        try:
            company = Company(symbol=symbol, source="VCI")
            data = company.events() if hasattr(company, "events") else None
            st.dataframe(data, use_container_width=True) if data is not None else st.warning("Không có dữ liệu sự kiện.")
        except Exception as exc:
            st.warning(f"Không tải được sự kiện {symbol}: {exc}")

    with tab7:
        try:
            q = Quote(symbol=symbol, source="VCI")
            price_hist_df = q.history(
                start=pd.to_datetime(start_date).strftime("%Y-%m-%d"),
                end=pd.to_datetime(end_date).strftime("%Y-%m-%d"),
                interval="1D",
            )
            st.dataframe(price_hist_df, use_container_width=True)
        except Exception as exc:
            st.warning(f"Không tải được giá niêm yết {symbol}: {exc}")

st.subheader("Danh sách công ty theo ngành")
if selected_industry == DEFAULT_CHOICE:
    st.info("Vui lòng chọn nhóm ngành.")
else:
    filtered = industry_df[industry_df["icb_name2"].str.contains(selected_industry, case=False, na=False)]

    if filtered.empty:
        st.warning(f"Không có công ty nào cho ngành: {selected_industry}")
    else:
        show = (
            filtered[["symbol", "organ_name", "icb_name2"]]
            .drop_duplicates()
            .sort_values("symbol")
            .reset_index(drop=True)
        )

        event = st.dataframe(
            show,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
            key="industry_table_select",
        )
        st.caption(f"Số mã trong ngành {selected_industry}: {len(show)}")

        selected_rows = event.selection.rows if event else []
        if selected_rows:
            row_idx = selected_rows[0]
            selected_symbol = str(show.iloc[row_idx]["symbol"])
            show_company_popup(selected_symbol)
        else:
            st.info("Bấm vào 1 dòng để mở popup.")

        


with right:
    st.metric("Điểm đóng cửa gần nhất", f"{df['close'].iloc[-1]:,.2f}")
    st.metric("Cao nhất", f"{df['high'].max():,.2f}")
    st.metric("Thấp nhất", f"{df['low'].min():,.2f}")
    st.metric("Số phiên", f"{len(df):,}")

# st.subheader("Dữ liệu chi tiết")
# st.dataframe(industry_df, use_container_width=True)
