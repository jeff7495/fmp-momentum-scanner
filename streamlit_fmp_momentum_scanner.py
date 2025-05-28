import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Pro-Style Momentum Scanner Grid", layout="wide")

st.title("📊 Pro-Style Momentum Scanner Grid")

if st.button("🚀 Scan Now"):
    API_KEY = st.secrets["FMP_API_KEY"]
    url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={API_KEY}"

    try:
        response = requests.get(url)
        gainers = response.json()
    except Exception as e:
        st.error(f"API error: {e}")
        st.stop()

    processed_data = []
    for g in gainers:
        if not isinstance(g, dict):
            continue

        try:
            price = float(g.get('price', 0))
            volume = int(g.get('volume', 0))
            changes_pct_raw = g.get('changesPercentage', '')
            changes_pct = str(changes_pct_raw).replace('%', '').replace('+', '').strip()
            changes_pct = float(changes_pct) if changes_pct else 0.0

            news_link = f"https://www.google.com/search?q={g.get('symbol', '')}+stock+news"

            processed_data.append({
                "Symbol": g.get("symbol", ""),
                "Price": price,
                "Volume": volume,
                "Change (%)": changes_pct,
                "News": f"[Search News]({news_link})"
            })
        except Exception as e:
            continue

    if not processed_data:
        st.info("No qualifying stocks found.")
    else:
        df = pd.DataFrame(processed_data)
        df = df.sort_values("Change (%)", ascending=False)
        st.dataframe(df, use_container_width=True)
