import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V5.0", page_icon="💎", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
    
    .sniper-zone { background-color: #fee2e2; padding: 15px; border-radius: 10px; border: 2px dashed #ef4444; text-align: center; }
    .investor-zone { background-color: #dcfce7; padding: 15px; border-radius: 10px; border: 2px dashed #22c55e; text-align: center; }
    .recommend-text { font-size: 1.2rem; font-weight: bold; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("💎 Polaris V5.0: The Ultimate Decision Engine")
st.markdown("**ระบบเทรดครบวงจร: สแกนหาหุ้น -> วิเคราะห์กราฟ -> วางแผนหน้าตัก**")
st.write("---")

# --- 2. ข้อมูลหุ้นและกองทุน (อัปเดตเพิ่มหุ้นใหม่) ---
STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", 
    "BDMS.BK", "PTTEP.BK",
    "TISCO.BK",  # ปันผลสูง
    "CPAXT.BK",  # แม็คโคร/โลตัส (ค้าปลีก)
    "CRC.BK",    # เซ็นทรัลรีเทล
    "CPN.BK"     # เซ็นทรัลพัฒนา (อสังหา)
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

# --- 3. ฟังก์ชันดึงข้อมูล (Core Engine) ---
@st.cache_data(ttl=3600)
def get_data_from_yahoo(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if len(df) < 100: return None, 0, 0

        # Indicators
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Volume MA
        df['VolMA'] = df['Volume'].rolling(20).mean()

        # Fundamental
        pe, div_yield = 0, 0
        try:
            info = yf.Ticker(ticker).info
            pe = info.get('trailingPE', 0)
            raw_div = info.get('dividendYield', 0)
            if raw_div is not None:
                temp_div = raw_div * 100 if raw_div < 1 else raw_div
                div_yield = 0 if temp_div > 20 else temp_div
        except: pass

        return df, pe, div_yield
    except: return None, 0, 0

@st.cache_data(ttl=300) 
def get_news_sentiment(ticker):
    try:
        news = yf.Ticker(ticker).news
        sentiment_score = 0
        positive = ['growth', 'profit', 'jump', 'rise', 'record', 'buy', 'bull', 'gain', 'strong', 'up', 'high', 'dividend']
        negative = ['loss', 'fall', 'drop', 'cut', 'lawsuit', 'bear', 'low', 'risk', 'miss', 'down', 'weak', 'plunge']
        
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
            cleaned_news.append({'title': title, 'link': n.get('link'), 'publisher': n.get('publisher'), 'score': score})
            
        final_sentiment = "⚪ Neutral"
        if sentiment_score > 0: final_sentiment = "🟢 Positive"
        elif sentiment_score < 0: final_sentiment = "🔴 Negative"
        
        return cleaned_news[:5], final_sentiment, sentiment_score
    except: return [], "⚪ Neutral", 0

# --- 4. Strategy Engine ---
def analyze_data(df, pe, div):
    price = df['Close'].iloc[-1]
    ema200 = df['EMA200'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    vol = df['Volume'].iloc[-1]
    vol_ma = df['VolMA'].iloc[-1]
    
    if price > ema200:
        trend = "ขาขึ้น 🐂"
        strategy = "⭐ ถือยาว"
    else:
        trend = "ขาลง 🐻"
        strategy = "⚡ เล่นสั้น"
    
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
    
    vol_status = "🔥 Vol พีค!" if vol > vol_ma * 1.5 else ""
    
    return price, rsi, trend, strategy, action, color, text_color, vol_status

# --- 5. Dashboard ---
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
                 column_order=cols, height=500, use_container_width=True)

    # --- 6. Deep Dive & Decision Support (ส่วนใหม่!) ---
    st.write("---")
    
    # แบ่งหน้าจอ: ซ้าย(กราฟ) - ขวา(คำนวณเงิน)
    col_chart, col_decision = st.columns([1.5, 1])
    
    with col_chart:
        st.subheader("🔍 Technical Chart")
        symbol_list = [d["Symbol"] for d in data_list]
        selected_symbol = st.selectbox("เลือกหุ้นเพื่อวิเคราะห์:", symbol_list)
        target = next((t for n, t in all_tickers if n.replace(".BK", "") == selected_symbol), None)

        if target:
            df_chart, _, _ = get_data_from_yahoo(target)
            if df_chart is not None:
                current_price_default = float(df_chart['Close'].iloc[-1])
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.7])
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                                low=df_chart['Low'], close=df_chart['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA200'], name='EMA 200', line=dict(color='blue', width=2)), row=1, col=1)
                colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in df_chart.iterrows()]
                fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
                fig.update_layout(height=600, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)
                
                # News Section
                st.markdown("#### 📰 ข่าวล่าสุด & อารมณ์ตลาด")
                news_list, sentiment_label, sentiment_score = get_news_sentiment(target)
                st.info(f"Market Sentiment: {sentiment_label} (Score: {sentiment_score})")
                
                if news_list:
                    for n in news_list:
                        icon = "🟢" if n['score'] > 0 else ("🔴" if n['score'] < 0 else "⚪")
                        st.markdown(f"{icon} [{n['title']}]({n['link']})")
                else:
                    st.caption("ไม่มีข่าวล่าสุดจาก Yahoo Finance")

    with col_decision:
        st.subheader("🧠 Decision Support (วางแผนเทรด)")
        
        # 1. กรอกต้นทุน (ถ้ามี)
        with st.expander("📝 บันทึกต้นทุน (ถ้ามีของ)", expanded=True):
            avg_cost = st.number_input("ต้นทุนเฉลี่ย (บาท)", value=0.0, step=0.1, format="%.2f")
            qty = st.number_input("จำนวนหุ้นที่มี", value=0, step=100)
            
            if qty > 0 and avg_cost > 0:
                market_val = current_price_default * qty
                cost_val = avg_cost * qty
                unrealized = market_val - cost_val
                pct = (unrealized / cost_val) * 100
                
                if unrealized >= 0:
                    st.success(f"กำไร: +{unrealized:,.0f} ฿ (+{pct:.2f}%)")
                    
                    # คำนวณขายเอาทุนคืน (Free Ride)
                    shares_sell = cost_val / current_price_default
                    st.markdown("##### 💡 ทางเลือกแก้เกม:")
                    st.write(f"- ขาย **{int(shares_sell):,} หุ้น** เพื่อเอาทุนคืนทั้งหมด")
                    st.write(f"- จะเหลือ **{int(qty - shares_sell):,} หุ้น** เป็นกำไรฟรีๆ (Profit Run)")
                else:
                    st.error(f"ขาดทุน: {unrealized:,.0f} ฿ ({pct:.2f}%)")
                    st.markdown("##### 💡 จุดถัวเฉลี่ย:")
                    st.write(f"- ถ้าซื้อเพิ่มเท่าตัว ต้นทุนใหม่จะอยู่ที่: **{(avg_cost + current_price_default)/2:.2f} ฿**")

        # 2. วิเคราะห์กลยุทธ์ (Sniper vs Investor)
        st.write("---")
        st.markdown("#### ⚖️ คำแนะนำ 2 มุมมอง")
        
        rsi_val = df_chart['RSI'].iloc[-1]
        
        # Sniper View
        sniper_msg = ""
        if rsi_val <= 30: sniper_msg = "🔫 **FIRE!**: ของถูกมาก สวนเทรนด์ได้"
        elif rsi_val >= 70: sniper_msg = "💰 **TAKE PROFIT**: ขายหมูดีกว่าติดดอย"
        elif sentiment_score < 0 and current_price_default < avg_cost: sniper_msg = "🚨 **CUT/WAIT**: ข่าวร้าย + ขาดทุน"
        else: sniper_msg = "⏳ **WAIT**: ยังไม่มีจังหวะคมๆ"
            
        st.markdown(f'<div class="sniper-zone"><b>Sniper (สั้น):</b><br>{sniper_msg}</div>', unsafe_allow_html=True)
        st.write("")
        
        # Investor View
        investor_msg = ""
        ema200_val = df_chart['EMA200'].iloc[-1]
        
        if current_price_default > ema200_val:
            investor_msg = "💎 **RUN TREND**: หุ้นเป็นขาขึ้น ถือต่อได้สบาย"
            if rsi_val <= 45: investor_msg += "<br>(จังหวะดีในการซื้อเพิ่ม)"
        else:
            investor_msg = "🛡️ **DEFENSIVE**: หลุดแนวรับสำคัญ เน้นถือเงินสด"
            if avg_cost > 0 and current_price_default < avg_cost * 0.9: investor_msg += "<br>(ถ้าพื้นฐานดี ทยอยสะสมได้)"
            
        st.markdown(f'<div class="investor-zone"><b>Investor (ยาว):</b><br>{investor_msg}</div>', unsafe_allow_html=True)

        # 3. เครื่องคิดเลขความเสี่ยง (RRR)
        st.write("---")
        st.markdown("#### 🧮 คำนวณความเสี่ยง (New Trade)")
        stop_loss_pct = st.slider("ยอมตัดขาดทุน (%)", 1, 10, 5)
        take_profit_pct = st.slider("หวังกำไร (%)", 1, 30, 10)
        
        stop_price = current_price_default * (1 - stop_loss_pct/100)
        target_price = current_price_default * (1 + take_profit_pct/100)
        
        reward = target_price - current_price_default
        risk = current_price_default - stop_price
        rrr = reward / risk if risk > 0 else 0
        
        col_r1, col_r2 = st.columns(2)
        col_r1.metric("จุดคัท (Stop)", f"{stop_price:.2f}")
        col_r2.metric("จุดขาย (Target)", f"{target_price:.2f}")
        
        if rrr >= 2:
            st.success(f"✅ **RRR = {rrr:.2f}** (คุ้มเสี่ยง!)")
        else:
            st.error(f"❌ **RRR = {rrr:.2f}** (ไม่คุ้ม!)")

else:
    st.error("โหลดข้อมูลไม่ได้ กรุณา Refresh")
