import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V4.1", page_icon="💎", layout="wide")

st.title("💎 Polaris V4.1: Intelligence Edition")
st.markdown("""
**ระบบตัดสินใจลงทุน: กราฟ (Technical) + งบ (Fundamental) + ข่าว (Sentiment)**
* 📊 **Strategy:** วิเคราะห์เทรนด์และจุดซื้อขาย
* 📰 **News Room:** เจาะลึกข่าวสารจากต้นตอ (SET / Yahoo)
""")
st.write("---")

# --- 2. ข้อมูลหุ้นและกองทุน ---
STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", 
    "BDMS.BK", "PTTEP.BK"
]

FUNDS = {
    "SCBSEMI (Semi-Conductor)": "SMH", 
    "SCBRMNDQ (Nasdaq-100)": "QQQ", 
    "SCBRMS&P500 (S&P 500)": "SPY", 
    "SCBGQUAL (Global Quality)": "QUAL", 
    "Gold (ทองคำโลก)": "GLD",
    "Silver (เงินโลก)": "SLV",
    "Apple (King)": "AAPL",
    "Nvidia (AI God)": "NVDA"
}

# --- 3. ฟังก์ชันดึงข้อมูล (Cache + Smart Filter) ---
@st.cache_data(ttl=3600) # จำค่าไว้ 1 ชม.
def get_data_from_yahoo(ticker):
    try:
        # ดึงกราฟ
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        if len(df) < 100: return None, 0, 0

        # คำนวณ Indicator
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # ดึงงบการเงิน + Sanity Check
        pe, div_yield = 0, 0
        try:
            info = yf.Ticker(ticker).info
            pe = info.get('trailingPE', 0)
            raw_div = info.get('dividendYield', 0)
            
            # Logic กรองค่าเพี้ยน
            if raw_div is not None:
                temp_div = raw_div * 100 if raw_div < 1 else raw_div
                if temp_div > 20: 
                    div_yield = 0 
                else:
                    div_yield = temp_div
        except: pass

        return df, pe, div_yield

    except: return None, 0, 0

# --- 4. ฟังก์ชันข่าวและอารมณ์ (News Intelligence) ---
@st.cache_data(ttl=300) 
def get_news_sentiment(ticker):
    try:
        news = yf.Ticker(ticker).news
        sentiment_score = 0
        news_count = 0
        
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
            news_count += 1
            
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

# --- 5. สมองกลวิเคราะห์ (Strategy Engine) ---
def analyze_data(df, pe, div):
    price = df['Close'].iloc[-1]
    ema200 = df['EMA200'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    
    # 1. Strategy Logic
    if price > ema200:
        trend = "ขาขึ้น 🐂"
        strategy = "⭐ ถือยาว (Run Trend)"
    else:
        trend = "ขาลง 🐻"
        strategy = "⚡ เล่นสั้น (Swing Trade)"
    
    # 2. Action Logic
    action = "⏳ Wait"
    color = "white"
    text_color = "black"
    
    if rsi <= 30:
        action = "🟢 BUY DIP"
        color = "#90EE90" # เขียวอ่อน
    elif rsi >= 70:
        action = "🔴 SELL"
        color = "#FFB6C1" # แดงอ่อน
    elif 30 < rsi < 45 and price > ema200:
        action = "➕ BUY MORE"
        color = "#98FB98"
        
    return price, rsi, trend, strategy, action, color, text_color

# --- 6. แสดงผล Dashboard ---
st.subheader("📊 Strategic Dashboard")

data_list = []
all_tickers = [(s, s) for s in STOCKS] + [(n, t) for n, t in FUNDS.items()]

my_bar = st.progress(0)

for i, (name, ticker) in enumerate(all_tickers):
    df, pe, div = get_data_from_yahoo(ticker)
    
    if df is not None:
        price, rsi, trend, strat, act, col, txt_col = analyze_data(df, pe, div)
        
        data_list.append({
            "Symbol": name.replace(".BK", ""),
            "Ticker": ticker, # เก็บไว้ใช้ดึงข่าว
            "Price": price,
            "RSI": rsi,
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
    # ตารางหลัก
    cols_show = ["Symbol", "Price", "RSI", "Strategy", "Action", "P/E", "Div %", "Trend"]
    
    def highlight_rows(row):
        bg_color = row.get("Color", "white")
        txt_color = row.get("TextColor", "black")
        return [f'background-color: {bg_color}; color: {txt_color}' for _ in cols_show]

    # แสดงตาราง
    st.dataframe(
        res_df.style.apply(highlight_rows, axis=1, subset=cols_show).format({"Price": "{:,.2f}", "RSI": "{:.1f}"}),
        column_order=cols_show,
        height=500,
        use_container_width=True
    )

    # --- 7. Deep Dive & News Room ---
    st.write("---")
    st.subheader("🔍 เจาะลึก (Chart & News)")
    
    col_sel, col_chart = st.columns([1, 2])
    
    with col_sel:
        st.markdown("##### เลือกหุ้นที่สนใจ")
        symbol_list = [d["Symbol"] for d in data_list]
        selected_symbol = st.selectbox("List", symbol_list, label_visibility="collapsed")
        
        # หาข้อมูลตัวที่เลือก
        selected_data = next((item for item in data_list if item["Symbol"] == selected_symbol), None)
        target_ticker = selected_data['Ticker']
        
        # ดึงข่าวและ Sentiment
        news_list, sentiment = get_news_sentiment(target_ticker)
        
        st.info(f"**Market Sentiment:** {sentiment}")
        
        # ปุ่มลิงก์ภายนอก (Magic Links)
        st.markdown("##### 🔗 แหล่งข่าวต้นทาง (Official Sources)")
        
        # ถ้าเป็นหุ้นไทย ให้ลิงก์ไป SET
        if ".BK" in target_ticker:
            clean_sym = target_ticker.replace(".BK", "")
            set_url = f"https://www.set.or.th/th/market/product/stock/quote/{clean_sym}/news"
            st.link_button(f"📢 ข่าวทางการ {clean_sym} (SET.or.th)", set_url, type="primary")
            
        # ลิงก์ Yahoo Finance / Google
        yahoo_url = f"https://finance.yahoo.com/quote/{target_ticker}/news"
        google_url = f"https://www.google.com/search?q={selected_symbol}+stock+news&tbm=nws"
        
        c1, c2 = st.columns(2)
        c1.link_button("Yahoo News", yahoo_url)
        c2.link_button("Google News", google_url)

        st.markdown("---")
        st.markdown("##### 🗞️ หัวข้อข่าวล่าสุด (AI Scan)")
        if news_list:
            for n in news_list:
                icon = "🟢" if n['score'] > 0 else ("🔴" if n['score'] < 0 else "⚪")
                st.markdown(f"{icon} [{n['title']}]({n['link']})")
        else:
            st.caption("ไม่มีข้อมูลข่าวล่าสุดจาก Feed")

    with col_chart:
        if selected_data:
            df_chart, _, _ = get_data_from_yahoo(target_ticker)
            if df_chart is not None:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'], name='Price', line=dict(color='black')))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA50'], name='EMA 50', line=dict(color='orange', width=1, dash='dot')))
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA200'], name='EMA 200', line=dict(color='blue', width=2)))
                fig.update_layout(title=f"Technical Chart: {selected_symbol}", height=600)
                st.plotly_chart(fig, use_container_width=True)

else:
    st.error("โหลดข้อมูลไม่ได้ กรุณา Refresh")
