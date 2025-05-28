import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Pro-Style Momentum Scanner", layout="wide")
st.title("📊 Pro-Style Momentum Scanner Grid")

FMP_API_KEY = st.secrets.get("FMP_API_KEY", "demo")  # Replace "demo" with your actual key or configure in Secrets

def fetch_top_gainers():
    url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={FMP_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch data from FMP API.")
        return []

def scan_pro_style():
    gainers = fetch_top_gainers()
    results = []

    for g in gainers:
        try:
            symbol = g.get("symbol", "")
            price = float(g.get("price", 0))
            volume = int(g.get("volume", 0))
            changes_percentage = str(g.get("changesPercentage", "0")).replace('%', '').replace('+', '').strip()
            change_pct = float(changes_percentage) if changes_percentage else 0
            news_url = f"https://www.google.com/search?q={symbol}+stock+news"

            results.append({
                "Symbol": symbol,
                "Price": price,
                "Volume": volume,
                "Change (%)": change_pct,
                "News": f"[🔍 News]({news_url})"
            })
        except Exception as e:
            st.warning(f"Skipping {g.get('symbol', 'unknown')} due to error: {e}")
            continue

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("Change (%)", ascending=False)
    return df

if st.button("🚀 Scan Now"):
    df = scan_pro_style()
    if df.empty:
        st.info("No qualifying stocks found.")
    else:
        st.dataframe(df, use_container_width=True)
