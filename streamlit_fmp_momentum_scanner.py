import streamlit as st
import pandas as pd
import requests
import os

# Load FMP API key from secrets
FMP_API_KEY = st.secrets["FMP_API_KEY"]

# Function to fetch top gainers from FMP API
def get_top_gainers():
    url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={FMP_API_KEY}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else []

# Function to build a DataFrame from the API response
def build_dataframe():
    gainers = get_top_gainers()
    data = []
    for g in gainers:
        try:
            symbol = g.get('symbol', '')
            price = float(g.get('price', 0))
            volume = int(g.get('volume', 0))
            change_pct = float(str(g.get('changesPercentage', '0')).replace('%', '').replace('+', '').strip())

            # Filter logic
            if change_pct < 10 or volume == 0:
                continue

            # Example float and rel vol for testing; replace with actual logic if available
            rel_vol = round(volume / 500000, 2)  # Example logic
            float_shares = round(50 + hash(symbol) % 50, 2)  # Fake float for demo purposes

            news_url = f"https://www.google.com/search?q={symbol}+stock+news"

            data.append({
                "Symbol": symbol,
                "Price": price,
                "Volume": f"{volume:,}",
                "Change (%)": change_pct,
                "Relative Volume": rel_vol,
                "Float (M)": float_shares,
                "News": f'<a href="{news_url}" target="_blank">🔗 News</a>'
            })
        except Exception as e:
            continue

    return pd.DataFrame(data)

# Streamlit UI
st.set_page_config(page_title="Pro-Style Momentum Scanner Grid", layout="wide")
st.title("📊 Pro-Style Momentum Scanner Grid")

if st.button("🚀 Scan Now"):
    df = build_dataframe()
    if not df.empty:
        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info("No qualifying stocks found.")
