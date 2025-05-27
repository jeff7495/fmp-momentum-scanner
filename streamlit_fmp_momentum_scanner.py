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
    try:
        url = f"https://financialmodelingprep.com/api/v3/gainers?apikey={FMP_API_KEY}"
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

def scan_with_feedback():
    gainers = get_top_gainers()
    st.subheader("🔍 Scanning These Gainers")
    st.write([g.get("ticker") for g in gainers if "ticker" in g])

    results = []
    for stock in gainers:
        try:
            ticker = stock.get("ticker", "N/A")
            price = float(stock.get("price", 0))
            change_pct = float(stock.get("changesPercentage", "0").replace("%", "").replace("+", ""))

            st.write(f"🧪 Checking {ticker}: Price=${price}, Change={change_pct}%")

            if not (PRICE_MIN <= price <= PRICE_MAX):
                st.write(f"⛔ {ticker} skipped: price out of range")
                continue
            if change_pct < PERCENT_CHANGE_MIN:
                st.write(f"⛔ {ticker} skipped: gain < {PERCENT_CHANGE_MIN}%")
                continue

            rvol = get_relative_volume(ticker)
            if rvol < REL_VOL_MIN:
                st.write(f"⛔ {ticker} skipped: RVOL {round(rvol, 2)} < {REL_VOL_MIN}")
                continue

            float_mil = get_float(ticker)
            if float_mil > FLOAT_MAX:
                st.write(f"⛔ {ticker} skipped: float {float_mil}M > {FLOAT_MAX}M")
                continue

            headline = get_news(ticker)
            if not headline:
                st.write(f"⛔ {ticker} skipped: no news found")
                continue

            results.append({
                "Ticker": ticker,
                "Price": price,
                "% Change": round(change_pct, 2),
                "Relative Volume": round(rvol, 2),
                "Float (M)": float_mil,
                "News Headline": headline,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            st.success(f"✅ {ticker} PASSED")
        except Exception as e:
            st.warning(f"⚠️ Error with {ticker}: {e}")
    return pd.DataFrame(results)

# Streamlit UI
st.title("🔍 FMP Momentum Scanner – Detailed Filter Log")

if st.button("Run Full Scan"):
    df = scan_with_feedback()
    if not df.empty:
        st.success("Qualifying Stocks Found:")
        st.dataframe(df)
    else:
        st.info("No stocks passed all filters.")
