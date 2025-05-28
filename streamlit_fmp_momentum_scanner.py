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

def scan_and_display():
    gainers = get_top_gainers()
    st.subheader("🔍 Gainers Being Scanned")
    st.code([g.get("ticker") for g in gainers if "ticker" in g])

    results = []
    for stock in gainers:
        try:
            ticker = stock.get("ticker", "N/A")
            price = float(stock.get("price", 0))
            change_pct = float(stock.get("changesPercentage", "0").replace("%", "").replace("+", ""))

            st.write(f"🧪 Checking {ticker}: Price=${price}, Change={change_pct}%")

            if not (PRICE_MIN <= price <= PRICE_MAX):
                continue
            if change_pct < PERCENT_CHANGE_MIN:
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
                "% Change": round(change_pct, 2),
                "Relative Volume": round(rvol, 2),
                "Float (M)": float_mil,
                "News Headline": headline,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            st.warning(f"⚠️ Error with {stock.get('ticker')}: {e}")

    return pd.DataFrame(results)

# Streamlit UI
st.set_page_config(page_title="Momentum Scanner", layout="wide")
st.title("📘 GUI Momentum Scanner with TradingView Export")

if st.button("Run Scan"):
    df = scan_and_display()
    if not df.empty:
        st.success(f"✅ {len(df)} Stocks Passed Filters")

        for _, row in df.iterrows():
            with st.container():
                st.markdown(
                    f'''
                    <div style="padding:15px; margin:10px 0; border:1px solid #ccc; border-radius:10px;">
                        <h3>{row['Ticker']} — ${row['Price']} ({row['% Change']}%)</h3>
                        <p><strong>RVOL:</strong> {row['Relative Volume']} | <strong>Float:</strong> {row['Float (M)']}M</p>
                        <p><em>News:</em> {row['News Headline']}</p>
                        <p><small>{row['Timestamp']}</small></p>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

        txt_content = "\n".join(df["Ticker"].tolist())
        st.download_button(
            label="📤 Export Watchlist to TradingView (.txt)",
            data=txt_content,
            file_name="tv_watchlist.txt",
            mime="text/plain"
        )
    else:
        st.info("No qualifying stocks found.")
