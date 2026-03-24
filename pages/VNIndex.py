###################################################

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import vnstock
from vnstock import Listing, Vnstock,Company
from vnstock.common import viz as _vnstock_viz  # noqa: F401 (registers .viz accessor)
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import os
from common import load_css, render_topbar

st.set_page_config(page_title="Greatfut - VNIndex & Stock Profile")
load_css()

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
    extra_class="topbar--vnindex",
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
    _nav_button("Bảng giá thị trường", "./dashboard.py")
with a2:
    _nav_button("Toàn cảnh thị trường", "pages/Toancanh_thitruong.py")
with a3:
    _nav_button("Danh sách các quỹ", "pages/Quymo.py")
with a4:
    _nav_button("Giá vàng", "pages/GoldPrice.py")

st.title("Greatfut - VNIndex & Stock Profile")




TABLE_NAME = "stocks"


def get_database_url():
    db_url = None
    try:
        db_url = st.secrets.get("DB_URL")
    except Exception:
        db_url = None
    if not db_url:
        db_url = os.getenv("DB_URL")
    if db_url:
        return db_url

    sql_server = os.getenv("SQL_SERVER", "localhost")
    sql_db = os.getenv("SQL_DB", "StockDB")
    sql_user = os.getenv("SQL_USER")
    sql_password = os.getenv("SQL_PASSWORD")

    if sql_user and sql_password:
        return f"mssql+pymssql://{sql_user}:{sql_password}@{sql_server}/{sql_db}"

    sql_driver = os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server")
    driver_param = sql_driver.replace(" ", "+")
    return (
        f"mssql+pyodbc://@{sql_server}/{sql_db}"
        f"?driver={driver_param}&trusted_connection=yes")


try:
    engine = create_engine(get_database_url())
except Exception as exc:
    st.error(f"Khong tao duoc ket noi CSDL: {exc}")
    st.stop()

# Lay danh sach ma HOSE tu vnstock
try:
    hose_symbols = (
        Listing(source="VCI")
        .symbols_by_exchange(exchange="HOSE")["symbol"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
except Exception as exc:
    st.error(f"Khong lay duoc danh sach ma HOSE: {exc}")
    st.stop()

# Lay danh sach ma co trong SQL
try:
    db_symbols_df = pd.read_sql(
        text(f"SELECT DISTINCT [symbol] FROM dbo.{TABLE_NAME}"),
        engine,
    )
except Exception as exc:
    st.error(f"Khong doc duoc danh sach ma tu SQL Server: {exc}")
    st.stop()

if db_symbols_df.empty:
    st.warning("Bang stocks dang trong.")
    st.stop()

db_symbols = db_symbols_df["symbol"].dropna().astype(str).unique().tolist()

# Chi hien thi ma thuoc HOSE va da co du lieu trong DB
available_symbols = sorted(set(hose_symbols).intersection(db_symbols))
if not available_symbols:
    st.warning("Khong co ma HOSE nao trong bang stocks.")
    st.stop()

selected_symbol = st.selectbox("Chọn mã cổ phiếu", available_symbols)
income_df = pd.DataFrame()


def _to_profile_df(raw):
    if raw is None:
        return pd.DataFrame()
    if isinstance(raw, pd.DataFrame):
        return raw.copy()
    if isinstance(raw, pd.Series):
        return raw.to_frame().T
    if isinstance(raw, dict):
        return pd.DataFrame([raw])
    if isinstance(raw, str):
        return pd.DataFrame({"description": [raw]})
    return pd.DataFrame()


def load_profile_df(symbol):
    method_candidates = ["profile", "overview", "company_profile", "info"]

    for class_name in ["Company", "Stock"]:
        cls = getattr(vnstock, class_name, None)
        if cls is None:
            continue

        instances = []
        try:
            instances.append(cls(symbol=symbol, source="VCI"))
        except Exception:
            pass
        try:
            instances.append(cls(symbol=symbol))
        except Exception:
            pass

        for instance in instances:
            for method_name in method_candidates:
                method = getattr(instance, method_name, None)
                if method is None or not callable(method):
                    continue
                try:
                    profile = _to_profile_df(method())
                    if not profile.empty:
                        return profile
                except Exception:
                    continue

    return pd.DataFrame()


profile_df = load_profile_df(selected_symbol)


def _to_df(raw):
    if raw is None:
        return pd.DataFrame()
    if isinstance(raw, pd.DataFrame):
        return raw.copy()
    if isinstance(raw, pd.Series):
        return raw.to_frame().T
    if isinstance(raw, dict):
        return pd.DataFrame([raw])
    if isinstance(raw, list):
        try:
            return pd.DataFrame(raw)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def load_shareholders_df(symbol):
    method_candidates = ["shareholders", "major_holders", "shareholder"]

    for class_name in ["Company", "Stock"]:
        cls = getattr(vnstock, class_name, None)
        if cls is None:
            continue

        instances = []
        try:
            instances.append(cls(symbol=symbol, source="VCI"))
        except Exception:
            pass
        try:
            instances.append(cls(symbol=symbol))
        except Exception:
            pass

        for instance in instances:
            for method_name in method_candidates:
                method = getattr(instance, method_name, None)
                if method is None or not callable(method):
                    continue
                try:
                    data = _to_df(method())
                    if not data.empty:
                        return data
                except Exception:
                    continue

    return pd.DataFrame()


shareholders_df = load_shareholders_df(selected_symbol)

# Lay du lieu gia cua ma duoc chon
query = text(
    f"""
    SELECT [time], [open], [high], [low], [close], [volume], [symbol]
    FROM dbo.{TABLE_NAME}
    WHERE [symbol] = :symbol
    ORDER BY [time] ASC
    """
)

price_df = pd.read_sql(query, engine, params={"symbol": selected_symbol})

if price_df.empty:
    st.warning(f"Khong co du lieu gia cho ma {selected_symbol}.")
    st.stop()

price_df["time"] = pd.to_datetime(price_df["time"], errors="coerce")
price_df = price_df.dropna(subset=["time"])

st.subheader(f"Giá biến động của cổ phiếu: {selected_symbol}")
df = price_df.copy()
fig = go.Figure(
    data=[
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            increasing_line_color="#16a34a",  # xanh la
            decreasing_line_color="#dc2626",  # do
            increasing_fillcolor="#16a34a",
            decreasing_fillcolor="#dc2626",
        )
    ]
)

fig.update_layout(
    xaxis_title="Ngày",
    yaxis_title="Giá",
    xaxis_rangeslider_visible=False,
    template="plotly_dark",
)

st.plotly_chart(fig, use_container_width=True)

# Them moi bieu do vnstock viz, giu nguyen chart cu
st.subheader(f"Biến động giá: {selected_symbol}")
try:
    selected_df = (
        price_df[price_df["symbol"].astype(str) == str(selected_symbol)]
        .copy()
        .sort_values("time")
    )
    ts_df = selected_df.set_index("time")
    ts_result = ts_df["close"].viz.timeseries(
        figsize=(10, 6),
        ylabel="Giá",
        xlabel="Thời gian",
        color_palette="vnstock",
        palette_shuffle=True,
    )
    ts_fig = None
    if isinstance(ts_result, tuple) and len(ts_result) >= 1:
        ts_fig = ts_result[0]
    elif hasattr(ts_result, "get_figure"):
        ts_fig = ts_result.get_figure()
    if ts_fig is not None:
        st.pyplot(ts_fig, use_container_width=True)
        plt.close(ts_fig)
except Exception as exc:
    st.info(f"Khong the ve bieu do vnstock viz: {exc}")

st.subheader(f"Giá biến động và khối lượng: {selected_symbol}")
try:
    combo_selected_df = (
        price_df[price_df["symbol"].astype(str) == str(selected_symbol)]
        .copy()
        .sort_values("time")
    )
    combo_df = combo_selected_df.set_index("time")
    try:
        combo_result = combo_df.viz.combo(
            bar_data="volume",
            line_data="close",
            left_ylabel="Khối lượng",
            right_ylabel="Giá",
            figsize=(10, 6),
            color_palette="stock",
            palette_shuffle=True,
        )
    except AttributeError:
        combo_result = combo_df.viz.combo_chart(
            bar_data="volume",
            line_data="close",
            left_ylabel="Volume (M)",
            right_ylabel="Price (K)",
            figsize=(10, 6),
            color_palette="stock",
            palette_shuffle=True,
        )

    combo_fig = None
    if isinstance(combo_result, tuple) and len(combo_result) >= 1:
        combo_fig = combo_result[0]
    elif hasattr(combo_result, "get_figure"):
        combo_fig = combo_result.get_figure()

    if combo_fig is not None:
        st.pyplot(combo_fig, use_container_width=True)
        plt.close(combo_fig)
except Exception as exc:
    st.info(f"Khong the ve combo viz: {exc}")

st.subheader(f"Heatmap lợi nhuận trung bình theo tháng: {selected_symbol}")
try:
    heatmap_df = (
        price_df[price_df["symbol"].astype(str) == str(selected_symbol)]
        .copy()
        .sort_values("time")
        .set_index("time")
    )
    heatmap_df["returns"] = pd.to_numeric(heatmap_df["close"], errors="coerce").pct_change() * 100
    heatmap_df = heatmap_df.dropna(subset=["returns"])

    return_pivot = pd.pivot_table(
        heatmap_df,
        index=heatmap_df.index.year,
        columns=heatmap_df.index.month,
        values="returns",
        aggfunc="mean",
    )
    if return_pivot.empty:
        raise ValueError("Khong du du lieu de tao heatmap.")

    heatmap_result = return_pivot.viz.heatmap(
        figsize=(10, 6),
        title=f"{selected_symbol} - Thống kê lợi nhuận trung bình theo tháng trong năm (%)",
        annot=True,
        cmap="RdYlGn",
    )

    heatmap_fig = None
    if isinstance(heatmap_result, tuple) and len(heatmap_result) >= 1:
        heatmap_fig = heatmap_result[0]
    elif hasattr(heatmap_result, "get_figure"):
        heatmap_fig = heatmap_result.get_figure()

    if heatmap_fig is not None:
        st.pyplot(heatmap_fig, use_container_width=True)
        plt.close(heatmap_fig)
except Exception as exc:
    st.info(f"Khong the ve heatmap loi nhuan: {exc}")

st.subheader(f"Mô tả công ty: {selected_symbol}")
try:
    company = Company(symbol=selected_symbol, source="VCI")
    if hasattr(company, "profile"):
        profile_df = company.profile()
    elif hasattr(company, "overview"):
        profile_df = company.overview()
    elif hasattr(company, "info"):
        profile_df = company.info()
    else:
        raise AttributeError("Company khong co profile/overview/info")

    profile_df.viz.wordcloud(
        figsize=(10, 6),
        title=f"{selected_symbol} - Mô tả công ty",
        max_words=50,
        color_palette="stock",
    )
    st.pyplot(plt.gcf(), clear_figure=True)
except Exception as exc:
    st.info(f"Khong the lay duoc mo ta cong ty: {exc}")


