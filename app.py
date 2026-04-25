import sqlite3
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
import requests

# ----------------------------------------
# CONFIGURATION
# ----------------------------------------
st.set_page_config(page_title="Financial Market Analysis", layout="wide")

# ----------------------------------------
# DATABASE CONNECTION
# ----------------------------------------
@st.cache_resource
def get_db_conn():
    conn = sqlite3.connect("market_analysis.db", check_same_thread=False)
    return conn

conn = get_db_conn()
cur = conn.cursor()

# ----------------------------------------
# CREATE TABLE
# ----------------------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS market_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date TIMESTAMP NOT NULL,
    open REAL, high REAL, low REAL, close REAL,
    volume REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# ----------------------------------------
# FUNCTIONS
# ----------------------------------------
def fetch_usd_to_ngn():
    """Fetch current USD/NGN rate with fallback."""
    try:
        res = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        rate = res.json()["rates"].get("NGN", 1600.0)
        return rate
    except Exception:
        return 1600.0  # fallback

USD_TO_NGN = fetch_usd_to_ngn()

def fetch_and_store_data(symbol="BTC-USD", period="5d", interval="15m"):
    data = yf.download(symbol, period=period, interval=interval)
    if data.empty:
        st.warning(f"No data returned for {symbol}")
        return
    for idx, row in data.iterrows():
        cur.execute("""
        INSERT OR IGNORE INTO market_prices (symbol, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol, idx.to_pydatetime(),
            float(row["Open"]), float(row["High"]),
            float(row["Low"]), float(row["Close"]),
            float(row["Volume"])
        ))
    conn.commit()

def load_data(symbol):
    df = pd.read_sql(f"SELECT * FROM market_prices WHERE symbol='{symbol}' ORDER BY date ASC;", conn)
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_indicators(df):
    df["SMA_20"] = df["close"].rolling(window=20).mean()
    df["SMA_50"] = df["close"].rolling(window=50).mean()
    df["RSI"] = compute_rsi(df["close"])
    df["Trend"] = df.apply(lambda x: "Bullish" if x["SMA_20"] > x["SMA_50"] else "Bearish", axis=1)
    return df

# ----------------------------------------
# PAGE CONTROL
# ----------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "selected_market" not in st.session_state:
    st.session_state.selected_market = None

# ----------------------------------------
# LANDING PAGE
# ----------------------------------------
if st.session_state.page == "landing":
    st.markdown("""
    <div style='text-align:center; margin-top:100px;'>
        <h1 style='font-size:48px; font-weight:bold;'>📚 DESIGN AN IMPLEMENTATION OF FINANCIAL MARKET ANALYSIS DATABASE FOR TRACKING STOCK PRICES AND TRADING TRENDS</h1>
        <h2 style='font-size:32px; font-weight:bold; margin-top:20px;'>A Case study of Nigerian exchange group (NGX)</h2>
        <h3 style='font-size:28px; margin-top:10px;'>Student: Prince Abumere Akhamiojie</h3>
        <h3 style='font-size:28px; margin-top:10px;'>Matric No: SW/HND/F23/0002</h3>
        <h3 style='font-size:28px; margin-top:10px;'>Supervisor: MR. JIMOH I.A.</h3>
        <h3 style='font-size:28px; margin-top:10px;'>School: FEDERAL POLYTECHNIC OFFA</h3>
    </div>
    """, unsafe_allow_html=True)
    if st.button("➡️ Go to Dashboard"):
        st.session_state.page = "dashboard"

# ----------------------------------------
# DASHBOARD PAGE (TABLE ONLY)
# ----------------------------------------
elif st.session_state.page == "dashboard":
    st.title("📊 Market Dashboard")

    symbols = ["BTC-USD", "ETH-USD", "AAPL", "MSFT", "TSLA", "EURUSD=X", "GBPUSD=X"]

    st.markdown("""
    <style>
    table {border-collapse: collapse; width: 95%; margin-bottom:20px;}
    th, td {border: 1px solid #ddd; padding: 10px; text-align: center;}
    th {background-color: #333; color: white;}
    tr:nth-child(even) {background-color: #f2f2f2;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<table><tr><th>Market</th><th>Price (USD)</th><th>Price (NGN)</th><th>Volume</th><th>Trend</th><th>Action</th></tr>", unsafe_allow_html=True)

    for symbol in symbols:
        df = load_data(symbol)
        if not df.empty:
            df = compute_indicators(df)
            latest = df.iloc[-1]
            price_usd = latest["close"]
            price_ngn = price_usd * USD_TO_NGN
            volume = latest["volume"]
            trend = latest["Trend"]
            trend_color = "green" if trend == "Bullish" else "red"
            action_label = "View Chart"
        else:
            price_usd = price_ngn = volume = "-"
            trend = "-"
            trend_color = "black"
            action_label = "Fetch Data"

        col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,2,2,2])
        col1.markdown(f"<b>{symbol}</b>", unsafe_allow_html=True)
        col2.markdown(f"${price_usd if price_usd=='-' else f'{price_usd:,.2f}'}", unsafe_allow_html=True)
        col3.markdown(f"₦{price_ngn if price_ngn=='-' else f'{price_ngn:,.2f}'}", unsafe_allow_html=True)
        col4.markdown(f"{volume if volume=='-' else f'{volume:,.0f}'}", unsafe_allow_html=True)
        col5.markdown(f"<span style='color:{trend_color}'>{trend}</span>", unsafe_allow_html=True)

        if col6.button(action_label, key=f"{symbol}_btn"):
            if action_label == "Fetch Data":
                with st.spinner(f"Fetching latest data for {symbol}..."):
                    fetch_and_store_data(symbol)
                    st.rerun()
            else:
                st.session_state.selected_market = symbol
                st.session_state.page = "analysis"
                st.rerun()

    st.markdown("</table>", unsafe_allow_html=True)

# ----------------------------------------
# MARKET ANALYSIS PAGE (CHART)
# ----------------------------------------
elif st.session_state.page == "analysis":
    symbol = st.session_state.selected_market
    st.header(f"📈 Market Analysis: {symbol}")
    df = load_data(symbol)

    if df.empty:
        st.warning("No data found. Please fetch it from dashboard first.")
        if st.button("⬅️ Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
    else:
        df = compute_indicators(df)
        latest = df.iloc[-1]

        if st.button("⬅️ Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()

        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            increasing_line_color='green', decreasing_line_color='red', name='Price'
        ))
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA_20"], line=dict(color='blue', width=2), name='SMA 20'))
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA_50"], line=dict(color='orange', width=2), name='SMA 50'))
        fig.add_trace(go.Bar(x=df["date"], y=df["volume"], marker_color='lightgrey', name='Volume', yaxis='y2'))

        fig.update_layout(
            title=f"{symbol} Market Chart",
            xaxis=dict(rangeslider=dict(visible=False), type="date"),
            yaxis=dict(title='Price'),
            yaxis2=dict(title='Volume', overlaying='y', side='right', showgrid=False),
            template='plotly_dark',
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Price (USD)", f"${latest['close']:.2f}")
        col2.metric("Price (NGN)", f"₦{latest['close']*USD_TO_NGN:,.2f}")
        col3.metric("Volume", f"{latest['volume']:,}")
        col4.metric("RSI", f"{latest['RSI']:.2f}")
        col5.metric("Trend", latest["Trend"])
