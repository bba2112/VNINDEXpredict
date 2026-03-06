import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from vnstock import Company

df = Company(symbol="ACB", source="VCI").history(start="2024-01-01", end="2024-06-30", interval="1D")

df['close'].viz.timeseries(figsize=(10, 6),
		title='Giá đóng cửa - Hợp đồng tương lai VN30F1M',
		ylabel='Giá',
		xlabel='Thời gian',
		color_palette='vnstock',
		palette_shuffle=True)