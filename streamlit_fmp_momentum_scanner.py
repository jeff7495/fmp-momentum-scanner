import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import yfinance as yf

# === CONFIG ===
FMP_API_KEY = st.secrets["FMP_API_KEY"]
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
PRICE_MIN = 1
PRICE_MAX = 20
PERCENT_CHANGE_MIN = 10
REL_VOL_MIN = 5
FLOAT_MAX = 10  # in millions

@st.cache_data
def get_top_gainers():
    url = f"https://financialmodelingprep.com/api/v3/gainers?apikey={FMP_API_KEY}"
    try:
        res = requests.get(url)
        data = res.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        st.error(f"FMP API Error: {e}")
        return []

@st.cache_data
def get_float(ticker):
    url = f"https://financialmodelingprep.com/api/v4/float-amount?symbol={ticker}&apikey={FMP_API_KEY}"
    try:
        res = requests.get(url)
        data = res.json()
        if isinstance(data, list) and data:
            return round(data[0].get("floatShares", 999_999_999) / 1_000_000, 2)
    except:
        pass
    return 999

@st.cache_data
def get_relative_volume(ticker, lookback=20):
    try:
        data = yf.download(ticker, period="30d", interval="1d", progress=False)
        if data.empty or "Volume" not in data.columns:
            return 0
        vol_series = data["Volume"].dropna()
        if vol_series.empty:
            return 0
        avg_vol = vol_series[-lookback:].mean()
        latest_vol = vol_series.iloc[-1]
        if pd.isna(latest_vol) or pd.isna(avg_vol) or avg_vol == 0:
            return 0
        return latest_vol / avg_vol
    except:
        return 0

@st.cache_data
def get_news(ticker):
    url = f"https://newsapi.org/v2/everything?q={ticker}&apiKey={NEWS_API_KEY}"
    try:
        r = requests.get(url)
        articles = r.json().get('articles', [])
        if articles:
            return articles[0]['title']
    except:
        pass
    return None

@st.cache_data
def scan_fmp_gainers():
    gainers = get_top_gainers()
    results = []

    for stock in gainers:
        try:
            ticker = stock.get('ticker')
            price = float(stock.get('price', 0))
            change_pct_str = stock.get('changesPercentage', '0').replace('%', '').replace('+', '')
            changes_percentage = float(change_pct_str)

            if not (PRICE_MIN <= price <= PRICE_MAX and changes_percentage >= PERCENT_CHANGE_MIN):
                continue

            rvol = get_relative_volume(ticker)
            if rvol < REL_VOL_MIN:
                continue

            float_mil = get_float(ticker)
            if float_mil > FLOAT_MAX:
                continue

            headline = get_news(ticker)
            if not headline:
                continue

            results.append({
                "Ticker": ticker,
                "Price": price,
                "% Change": round(changes_percentage, 2),
                "Relative Volume": round(rvol, 2),
                "Float (M)": float_mil,
                "News Headline": headline,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            st.warning(f"Error with {ticker}: {e}")

    return pd.DataFrame(results)

# === STREAMLIT UI ===
st.title("📈 FMP-Based Momentum Scanner (Ross Cameron Style)")

if st.button("🚀 Scan Top Gainers"):
    df = scan_fmp_gainers()
    if not df.empty:
        st.success("Momentum stocks found:")
        st.dataframe(df)
    else:
        st.info("No qualifying stocks found.")
