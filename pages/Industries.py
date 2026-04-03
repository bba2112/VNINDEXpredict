from datetime import date

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from vnstock import Company,Vnstock,Trading
from common import load_css
from vnstock.explorer.misc.gold_price import * 
from vnstock.explorer.misc.exchange_rate import *

from vnstock import Company
company = Company(symbol='BID', source='VCI')
profile_df = company.profile()
st.write(profile_df)