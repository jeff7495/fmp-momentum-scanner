import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Pro-Style Momentum Scanner Grid", layout="wide")
st.title("📊 Pro-Style Momentum Scanner Grid")

FMP_API_KEY = st.secrets["FMP_API_KEY"]
SHOW_GAP = st.sidebar.checkbox("Show Gap %", value=True)
SHOW_NEWS = st.sidebar.checkbox("Include News Links", value=True)

def get_gainers():
    url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={FMP_API_KEY}"
    res = requests.get(url)
    return res.json() if res.ok else []

def get_profile(symbol):
    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FMP_API_KEY}"
    res = requests.get(url)
    return res.json()[0] if res.ok and res.json() else {}

def get_news_link(symbol):
    return f"https://www.google.com/search?q={symbol}+stock+news"

def scan_pro_style():
    gainers = get_gainers()
    rows = []
    for g in gainers:
    if not isinstance(g, dict):
        continue  # Skip if g is not a dictionary

    change_pct_raw = g.get('changesPercentage', '')
    change_pct = str(change_pct_raw).replace('%','').replace('+','').strip()

        try:
            change_pct = float(change_pct)
        except:
            continue
        vol = g.get('volume', 0)
        float_m = profile.get('mktCap', 0) / profile.get('volAvg', 1e6) if profile else 0
        prev_close = profile.get('previousClose', None)
        gap_pct = None
        if SHOW_GAP and prev_close and prev_close > 0:
            try:
                gap_pct = round(((price - prev_close) / prev_close) * 100, 2)
            except:
                gap_pct = None

        rows.append({
            "Symbol": sym,
            "Price": price,
            "% Change": change_pct,
            "Volume": vol,
            "Float (M)": round(profile.get("volAvg", 0) / 1e6, 2) if profile else None,
            "Gap %": gap_pct if SHOW_GAP else None,
            "News": f"[📰]({get_news_link(sym)})" if SHOW_NEWS else ""
        })

    df = pd.DataFrame(rows)
    return df

if st.button("🚀 Scan Now"):
    df = scan_pro_style()
    if df.empty:
        st.info("No qualifying stocks found.")
    else:
        df_display = df.dropna(axis=1, how="all")
        st.dataframe(df_display.sort_values("% Change", ascending=False), use_container_width=True)
