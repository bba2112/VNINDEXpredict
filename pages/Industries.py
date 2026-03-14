import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from vnstock import Company,Vnstock

profile_df = Vnstock(symbol="VCB", source="VCI").profile()	

print(profile_df.viz.wordcloud(figsize=(10, 6), 
                         title='VCB - Mô tả công ty',
                         max_words=50,
                         color_palette='stock'))