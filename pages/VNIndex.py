###################################################

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import vnstock
from vnstock import Listing
from vnstock.common import viz as _vnstock_viz  # noqa: F401 (registers .viz accessor)
import plotly.graph_objects as go
import matplotlib.pyplot as plt

st.title("VNSTOCK Dashboard")

theme_mode = st.sidebar.selectbox("Tone nền", ["Sáng", "Tối"], index=0)
is_dark_theme = theme_mode == "Tối"
plotly_template = "plotly_dark" if is_dark_theme else "plotly_white"

if is_dark_theme:
    plt.style.use("dark_background")
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #0f1117;
            color: #f3f4f6;
        }
        [data-testid="stSidebar"] {
            background-color: #111827;
        }
        [data-testid="stSidebar"] * {
            color: #f3f4f6 !important;
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    plt.style.use("default")
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #ffffff;
            color: #111827;
        }
        [data-testid="stSidebar"] {
            background-color: #f9fafb;
        }
        [data-testid="stSidebar"] * {
            color: #111827 !important;
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


SQL_SERVER = "localhost"
SQL_DB = "StockDB"
TABLE_NAME = "stocks"


engine = create_engine(
    f"mssql+pyodbc://@{SQL_SERVER}/{SQL_DB}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
)

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
    template=plotly_template,
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

st.subheader(f"Cổ đông lớn: {selected_symbol}")
try:
    if shareholders_df is None or shareholders_df.empty:
        raise ValueError("shareholders_df chưa có dữ liệu.")

    pie_df = shareholders_df.copy()
    if "share_holder" not in pie_df.columns:
        if "shareholder" in pie_df.columns:
            pie_df = pie_df.rename(columns={"shareholder": "share_holder"})
        elif "holder" in pie_df.columns:
            pie_df = pie_df.rename(columns={"holder": "share_holder"})

    if "share_own_percent" not in pie_df.columns:
        if "ownership_percent" in pie_df.columns:
            pie_df = pie_df.rename(columns={"ownership_percent": "share_own_percent"})
        elif "ownership" in pie_df.columns:
            pie_df = pie_df.rename(columns={"ownership": "share_own_percent"})

    required_cols = ["share_holder", "share_own_percent"]
    missing_cols = [col for col in required_cols if col not in pie_df.columns]
    if missing_cols:
        raise ValueError(f"Thiếu cột dữ liệu: {', '.join(missing_cols)}")

    pie_df["share_own_percent"] = pd.to_numeric(pie_df["share_own_percent"], errors="coerce")
    pie_df = pie_df.dropna(subset=["share_own_percent"])
    if pie_df.empty:
        raise ValueError("Khong co du lieu ty le so huu hop le.")

    pie_plot_df = pie_df.set_index("share_holder")
    try:
        pie_result = pie_plot_df.viz.pie(
            y="share_own_percent",
            title=f"Cổ đông lớn {selected_symbol}",
            figsize=(10, 6),
            ylabel="",
            color_palette="stock",
        )
    except Exception:
        pie_result = pie_df.viz.pie(
            title=f"Cổ đông lớn {selected_symbol}",
            labels="share_holder",
            values="share_own_percent",
            figsize=(10, 6),
            ylabel="",
            color_palette="stock",
        )

    pie_fig = None
    if isinstance(pie_result, tuple) and len(pie_result) >= 1:
        pie_fig = pie_result[0]
    elif hasattr(pie_result, "get_figure"):
        pie_fig = pie_result.get_figure()

    if pie_fig is not None:
        st.pyplot(pie_fig, use_container_width=True)
        plt.close(pie_fig)
except Exception as exc:
    st.info(f"Khong the ve pie co dong lon: {exc}")
