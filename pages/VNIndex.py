###################################################

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from vnstock import Listing
from vnstock.common import viz as _vnstock_viz  # noqa: F401 (registers .viz accessor)
import plotly.graph_objects as go
import matplotlib.pyplot as plt

st.title("VNSTOCK Dashboard")


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

selected_symbol = st.selectbox("Chon ma VNIndex", available_symbols)

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

st.subheader(f"Gia bieu dong co phieu: {selected_symbol}")
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
    xaxis_title="Ngay",
    yaxis_title="Gia",
    xaxis_rangeslider_visible=False,
    template="plotly_white",
)

st.plotly_chart(fig, use_container_width=True)

# Them moi bieu do vnstock viz, giu nguyen chart cu
st.subheader("Biến động giá")
try:
    ts_df = df.sort_values("time").set_index("time")
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

st.subheader("Gia dong cua va khoi luong (vnstock viz)")
try:
    combo_df = df.sort_values("time").set_index("time")
    try:
        combo_result = combo_df.viz.combo(
            bar_data="volume",
            line_data="close",
            title="Gia dong cua va khoi luong giao dich - Hop dong tuong lai VN30F1M",
            left_ylabel="Volume (M)",
            right_ylabel="Price (K)",
            figsize=(10, 6),
            color_palette="stock",
            palette_shuffle=True,
        )
    except AttributeError:
        combo_result = combo_df.viz.combo_chart(
            bar_data="volume",
            line_data="close",
            title="Gia dong cua va khoi luong giao dich - Hop dong tuong lai VN30F1M",
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

st.subheader("Du lieu chi tiet")
st.dataframe(price_df, use_container_width=True)

st.caption(f"So dong du lieu: {len(price_df)}")
