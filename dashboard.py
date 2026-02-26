import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from vnstock import Listing

SQL_SERVER = "localhost"
SQL_DB = "StockDB"
TABLE_NAME = "stocks"

st.title("VNSTOCK Dashboard")

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
    st.error(f"Không lấy được danh sách mã HOSE: {exc}")
    st.stop()

# Lay danh sach ma co trong SQL
try:
    db_symbols_df = pd.read_sql(
        text(f"SELECT DISTINCT [symbol] FROM dbo.{TABLE_NAME}"),
        engine,
    )
except Exception as exc:
    st.error(f"Không đọc được danh sách mã từ SQL Server: {exc}")
    st.stop()

if db_symbols_df.empty:
    st.warning("Bảng stocks đang trống.")
    st.stop()

db_symbols = db_symbols_df["symbol"].dropna().astype(str).unique().tolist()

# Chi hien thi ma thuoc HOSE va da co du lieu trong DB
available_symbols = sorted(set(hose_symbols).intersection(db_symbols))
if not available_symbols:
    st.warning("Không có mã HOSE nào trong bảng stocks.")
    st.stop()

selected_symbol = st.selectbox("Chọn mã HOSE", available_symbols)

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
    st.warning(f"Không có dữ liệu giá cho mã {selected_symbol}.")
    st.stop()

price_df["time"] = pd.to_datetime(price_df["time"], errors="coerce")
price_df = price_df.dropna(subset=["time"])

st.subheader(f"Bảng Giá Đóng Cửa - {selected_symbol}")
st.line_chart(price_df.set_index("time")["close"])

st.subheader("Dữ liệu chi tiết")
st.dataframe(price_df, use_container_width=True)

st.caption(f"Số dòng dữ liệu: {len(price_df)}")
