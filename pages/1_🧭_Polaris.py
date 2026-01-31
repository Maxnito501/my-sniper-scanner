import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V5.2", page_icon="🛡️", layout="wide")

st.title("🛡️ Polaris V5.2: World-Class Trader Edition")
st.markdown("""
**ระบบเทรดมาตรฐานกองทุน: กราฟ + พื้นฐาน + ข่าว + บริหารหน้าตัก (Money Management)**
* 📊 **Analysis:** Technical & Fundamental & Volume
* 🛡️ **Risk Control:** Position Sizing Calculator (คำนวณจุดซื้อ-ขาย ตาม % ความเสี่ยง)
* 🌍 **Macro View:** ดูค่าเงินและพันธบัตร (ทิศทางลม)
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

# --- 3. ฟังก์ชันดึงข้อมูล (Macro + Stock) ---
@st.cache_data(ttl=3600)
def get_data_from_yahoo(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        if len(df) < 100: return None, 0, 0

        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['VolMA'] = df['Volume'].rolling(20).mean()

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

def get_macro_data():
    try:
        tickers = ["^TNX", "DX-Y.NYB", "THB=X"] 
        df = yf.download(tickers, period="5d", interval="1d", progress=False)['Close']
        return df.iloc[-1]
    except: return None

# --- 4. News Function ---
@st.cache_data(ttl=300) 
def get_news_sentiment(ticker):
    return [], "⚪ Neutral" 

# --- 5. Strategy Engine ---
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

# --- 6. Dashboard ---
st.subheader("🌍 Global Macro View (ทิศทางลม)")
macro_data = get_macro_data()
if macro_data is not None:
    m1, m2, m3 = st.columns(3)
    m1.metric("🇺🇸 US 10Y Bond Yield", f"{macro_data['^TNX']:.2f}%", help="ถ้าพุ่งแรง หุ้นเทคฯ มักจะร่วง")
    m2.metric("💵 Dollar Index (DXY)", f"{macro_data['DX-Y.NYB']:.2f}", help="ถ้าดอลลาร์แข็ง บาทจะอ่อน เงินไหลออก")
    m3.metric("🇹🇭 USD/THB", f"{macro_data['THB=X']:.2f} ฿", help="บาทอ่อนดีต่อส่งออก แย่ต่อ Fund Flow")
st.write("---")

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

    # --- 7. Deep Dive & Risk Calculator ---
    st.write("---")
    col_chart, col_tools = st.columns([2, 1])
    
    # ส่วนกราฟ
    with col_chart:
        st.subheader("🔍 Technical Chart")
        symbol_list = [d["Symbol"] for d in data_list]
        selected_symbol = st.selectbox("เลือกหุ้น:", symbol_list)
        target = next((t for n, t in all_tickers if n.replace(".BK", "") == selected_symbol), None)
        
        # ดึงราคาปัจจุบันมาเป็น Default ให้เครื่องคิดเลข
        current_price_default = 0.0
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
                fig.update_layout(height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

    # ส่วนเครื่องคิดเลข (กลับมาใช้แบบ % Slider ตาม V5.0)
    with col_tools:
        st.subheader("🛡️ Risk Calculator")
        
        with st.expander("🧮 คำนวณจุดซื้อ-ขาย (Position Sizing)", expanded=True):
            st.info("💡 **แผนการเทรด:** ใส่ราคาซื้อ แล้วปรับ % ตามความเสี่ยงที่รับไหว")
            
            # รับค่าราคา (Default เป็นราคาปัจจุบันของหุ้นที่เลือกซ้ายมือ)
            entry_price = st.number_input("ราคาเข้าซื้อ (Entry Price)", value=current_price_default, format="%.2f")
            
            # Slider ปรับ % (แบบ V5.0)
            stop_loss_pct = st.slider("ยอมตัดขาดทุนที่ (%)", 1, 15, 5)   # Default 5%
            take_profit_pct = st.slider("หวังกำไรที่ (%)", 1, 50, 10)    # Default 10%
            
            st.write("---")
            
            if entry_price > 0:
                # คำนวณราคา
                stop_price = entry_price * (1 - stop_loss_pct/100)
                target_price = entry_price * (1 + take_profit_pct/100)
                
                # คำนวณ Risk/Reward
                risk_amt = entry_price - stop_price
                reward_amt = target_price - entry_price
                rrr = reward_amt / risk_amt if risk_amt > 0 else 0
                
                # แสดงผล
                st.markdown(f"🛑 **จุดหนีตาย (Stop Loss):** `{stop_price:,.2f}`")
                st.markdown(f"🎯 **จุดขายทำกำไร (Take Profit):** `{target_price:,.2f}`")
                
                # วิเคราะห์ความคุ้มค่า
                if rrr >= 2:
                    st.success(f"✅ **RRR = {rrr:.2f}** (คุ้มเสี่ยง! ลุยได้)")
                else:
                    st.error(f"❌ **RRR = {rrr:.2f}** (ได้ไม่คุ้มเสีย อย่าเล่น)")
                
                st.caption(f"ถ้าซื้อ 10,000 บาท: เสี่ยงเสีย {10000*stop_loss_pct/100:,.0f} บ. / ลุ้นได้ {10000*take_profit_pct/100:,.0f} บ.")

else:
    st.error("โหลดข้อมูลไม่ได้ กรุณา Refresh")
