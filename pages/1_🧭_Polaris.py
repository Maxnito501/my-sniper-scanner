import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V4.4", page_icon="💎", layout="wide")

st.title("💎 Polaris V4.4: Expanded Universe")
st.markdown("""
**ระบบตัดสินใจลงทุน: เพิ่มหุ้นแกร่ง (Central / TISCO / Global Tech)**
* 📊 **Strategy:** วิเคราะห์เทรนด์และจุดซื้อขาย
* 🛡️ **Defense:** เน้นหุ้นปันผลสูงและพื้นฐานแกร่ง (Defensive Stocks)
""")
st.write("---")

# --- 2. ข้อมูลหุ้นและกองทุน (เพิ่มตัวใหม่!) ---
STOCKS = [
    # ของเดิม
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", "SCB.BK", 
    "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK", "PTTEP.BK",
    # เพิ่มใหม่ (New Gems) 💎
    "TISCO.BK",  # ปันผลเทพ
    "CPN.BK",    # เซ็นทรัลพัฒนา (ค่าเช่า)
    "CRC.BK"     # เซ็นทรัลรีเทล (ค้าปลีก)
]

FUNDS = {
    # Tech & Growth
    "SCBSEMI (Semi-Conductor)": "SMH", 
    "SCBRMNDQ (Nasdaq-100)": "QQQ", 
    "SCBRMS&P500 (S&P 500)": "SPY", 
    # Stock Picking (เพิ่มหุ้นนอกรายตัว)
    "Apple (The King)": "AAPL",
    "Nvidia (AI God)": "NVDA",
    "Microsoft (AI Father)": "MSFT", # <--- ใหม่
    "Coca-Cola (Defensive)": "KO",   # <--- ใหม่
    # Others
    "SCBGQUAL (Global Quality)": "QUAL", 
    "Gold (ทองคำโลก)": "GLD",
    "Silver (เงินโลก)": "SLV"
}

# --- 3. ฟังก์ชันดึงข้อมูล (Cache + Smart Filter) ---
@st.cache_data(ttl=3600) # จำค่าไว้ 1 ชม.
def get_data_from_yahoo(ticker):
    try:
        # ดึงกราฟรวม Volume
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        if len(df) < 100: return None, 0, 0

        # Technical Indicators
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Volume Moving Average
        df['VolMA'] = df['Volume'].rolling(20).mean()

        # Fundamental
        pe, div_yield = 0, 0
        try:
            info = yf.Ticker(ticker).info
            pe = info.get('trailingPE', 0)
            raw_div = info.get('dividendYield', 0)
            
            if raw_div is not None:
                temp_div = raw_div * 100 if raw_div < 1 else raw_div
                div_yield = 0 if temp_div > 20 else temp_div # Filter Error
        except: pass

        return df, pe, div_yield

    except: return None, 0, 0

# --- 4. News Function ---
@st.cache_data(ttl=300) 
def get_news_sentiment(ticker):
    try:
        news = yf.Ticker(ticker).news
        sentiment_score = 0
        
        positive = ['growth', 'profit', 'jump', 'rise', 'record', 'buy', 'bull', 'gain', 'strong', 'up', 'high', 'dividend', 'launch']
        negative = ['loss', 'fall', 'drop', 'cut', 'lawsuit', 'bear', 'low', 'risk', 'miss', 'down', 'weak', 'plunge', 'warn']
        
        cleaned_news = []
        for n in news:
            title = n.get('title', '')
            if not title: continue
            
            score = 0
            for w in positive: 
                if w in title.lower(): score += 1
            for w in negative: 
                if w in title.lower(): score -= 1
            
            sentiment_score += score
            cleaned_news.append({
                'title': title,
                'link': n.get('link'),
                'publisher': n.get('publisher'),
                'score': score
            })
            
        final_sentiment = "⚪ Neutral"
        if sentiment_score > 0: final_sentiment = "🟢 Positive"
        elif sentiment_score < 0: final_sentiment = "🔴 Negative"
        
        return cleaned_news[:5], final_sentiment
    except:
        return [], "⚪ Neutral"

# --- 5. Strategy Engine (Volume + Trend) ---
def analyze_data(df, pe, div):
    price = df['Close'].iloc[-1]
    ema200 = df['EMA200'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    vol = df['Volume'].iloc[-1]
    vol_ma = df['VolMA'].iloc[-1]
    
    # Strategy
    if price > ema200:
        trend = "ขาขึ้น 🐂"
        strategy = "⭐ ถือยาว"
    else:
        trend = "ขาลง 🐻"
        strategy = "⚡ เล่นสั้น"
    
    # Action & Colors
    action = "Wait"
    color = "white"
    text_color = "black"
    
    if rsi <= 30:
        action = "🟢 BUY DIP"
        color = "#90EE90"
    elif rsi >= 70:
        action = "🔴 SELL"
        color = "#FFB6C1"
    elif 30 < rsi < 45 and price > ema200:
        action = "➕ BUY MORE"
        color = "#98FB98"
    
    # Volume Analysis
    vol_status = "🔥 Vol พีค!" if vol > vol_ma * 1.5 else ""
    
    return price, rsi, trend, strategy, action, color, text_color, vol_status

# --- 6. Dashboard ---
st.subheader("📊 Strategic Dashboard")

data_list = []
all_tickers = [(s, s) for s in STOCKS] + [(n, t) for n, t in FUNDS.items()]
my_bar = st.progress(0)

for i, (name, ticker) in enumerate(all_tickers):
    df, pe, div = get_data_from_yahoo(ticker)
    
    if df is not None:
        price, rsi, trend, strat, act, col, txt_col, vol_st = analyze_data(df, pe, div)
        
        data_list.append({
            "Symbol": name.replace(".BK", ""),
            "Ticker": ticker,
            "Price": price,
            "RSI": rsi,
            "Vol": vol_st, 
            "Strategy": strat,
            "Action": act,
            "P/E": f"{pe:.1f}" if pe > 0 else "-",
            "Div %": f"{div:.2f}%" if div > 0 else "-",
            "Trend": trend,
            "Color": col,
            "TextColor": txt_col
        })
    my_bar.progress((i + 1) / len(all_tickers))
my_bar.empty()

if data_list:
    res_df = pd.DataFrame(data_list)
    cols = ["Symbol", "Price", "RSI", "Vol", "Strategy", "Action", "P/E", "Div %", "Trend"]
    
    def highlight_rows(row):
        bg_color = row.get("Color", "white")
        txt_color = row.get("TextColor", "black")
        return [f'background-color: {bg_color}; color: {txt_color}'] * len(row)

    st.dataframe(res_df.style.apply(highlight_rows, axis=1).format({"Price": "{:,.2f}", "RSI": "{:.1f}"}),
                 column_order=cols, height=600, use_container_width=True)

    # --- 7. Deep Dive & Tools ---
    st.write("---")
    col_chart, col_news = st.columns([2, 1])
    
    with col_news:
        st.subheader("📰 ข่าว & อารมณ์ตลาด")
        symbol_list = [d["Symbol"] for d in data_list]
        selected_symbol = st.selectbox("เลือกหุ้น:", symbol_list)
        target = next((t for n, t in all_tickers if n.replace(".BK", "") == selected_symbol), None)

        if target:
            news_list, sentiment = get_news_sentiment(target)
            st.info(f"Sentiment: {sentiment}")
            
            # ปุ่มลิงก์
            if ".BK" in target:
                clean_sym = target.replace(".BK", "")
                st.link_button(f"📢 ข่าว {clean_sym} (SET)", f"https://www.set.or.th/th/market/product/stock/quote/{clean_sym}/news", type="primary")
            else:
                st.link_button("Yahoo News", f"https://finance.yahoo.com/quote/{target}/news")

    with col_chart:
        st.subheader("🔍 Technical Chart")
        if target:
            df_chart, _, _ = get_data_from_yahoo(target)
            if df_chart is not None:
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.7])
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                                low=df_chart['Low'], close=df_chart['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA200'], name='EMA 200', line=dict(color='blue', width=2)), row=1, col=1)
                colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in df_chart.iterrows()]
                fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
                fig.update_layout(height=500, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
else:
    st.error("โหลดข้อมูลไม่ได้ กรุณา Refresh")
