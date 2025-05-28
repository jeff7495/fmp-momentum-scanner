import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import yfinance as yf

FMP_API_KEY = st.secrets["FMP_API_KEY"]
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

PRICE_MIN = 1
PRICE_MAX = 20
PERCENT_CHANGE_MIN = 10
REL_VOL_MIN = 5
FLOAT_MAX = 10

@st.cache_data
def get_top_gainers():
    url = f"https://financialmodelingprep.com/api/v3/gainers?apikey={FMP_API_KEY}"
    try:
        res = requests.get(url)
        data = res.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        st.error(f"FMP error: {e}")
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
        if (
            pd.isna(latest_vol)
            or pd.isna(avg_vol)
            or avg_vol == 0
            or isinstance(latest_vol, pd.Series)
            or isinstance(avg_vol, pd.Series)
        ):
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

def scan_pro_style():
    gainers = get_top_gainers()
    results = []
    for stock in gainers:
        try:
            ticker = stock.get("ticker", "N/A")
            price = float(stock.get("price", 0))
            change_pct = float(stock.get("changesPercentage", "0").replace("%", "").replace("+", ""))
            if not (PRICE_MIN <= price <= PRICE_MAX) or change_pct < PERCENT_CHANGE_MIN:
                continue
            rvol = get_relative_volume(ticker)
            if rvol < REL_VOL_MIN:
                continue
            float_mil = get_float(ticker)
            if float_mil > FLOAT_MAX:
                continue
            news = get_news(ticker)
            results.append({
                "% Change": round(change_pct, 2),
                "Symbol": ticker,
                "Price": price,
                "Float (M)": float_mil,
                "Relative Volume": round(rvol, 2),
                "News": news or "N/A",
                "Time": datetime.now().strftime("%H:%M:%S")
            })
        except Exception as e:
            st.warning(f"Error on {stock.get('ticker')}: {e}")
    return pd.DataFrame(results).sort_values("% Change", ascending=False)

# --- Streamlit UI ---
st.set_page_config(page_title="Pro Momentum Grid", layout="wide")
st.title("📊 Pro-Style Momentum Scanner Grid")

if st.button("🚀 Scan Now"):
    df = scan_pro_style()
    if not df.empty:
        st.dataframe(
            df.style
              .background_gradient(cmap="Greens", subset=["% Change"])
              .background_gradient(cmap="Blues", subset=["Float (M)"])
              .format({"Price": "${:.2f}", "% Change": "{:.2f}%", "Float (M)": "{:.2f}M", "Relative Volume": "{:.2f}"}),
            use_container_width=True
        )
        st.download_button("💾 Export to CSV", df.to_csv(index=False), "momentum_results.csv")
    else:
        st.info("No qualifying stocks found.")
