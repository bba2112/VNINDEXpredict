from datetime import date

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from vnstock import Company,Vnstock
from common import load_css
from vnstock.explorer.misc.gold_price import * 
from vnstock.explorer.misc.exchange_rate import *

def today_str() -> str:
    return date.today().isoformat()
cr = vcb_exchange_rate(date = today_str())

st.title ("Tỷ giá ngoại tệ")
st.dataframe(cr)

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
    