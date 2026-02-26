import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from vnstock import Quote,Listing,Company


listing = Listing(source="VCI")

print(listing.symbols_by_group("UPCOM"))