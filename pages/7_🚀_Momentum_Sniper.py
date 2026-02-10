import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Momentum Sniper (High Risk)", page_icon="🚀", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
    
    .bull-box { background-color: #dcfce7; padding: 15px; border-radius: 10px; border: 2px solid #16a34a; text-align: center; }
    .bear-box { background-color: #fee2e2; padding: 15px; border-radius: 10px; border: 2px solid #dc2626; text-align: center; }
    .target-box { background-color: #f0f9ff; padding: 15px; border-radius: 10px; border: 2px solid #0ea5e9; text-align: center; }
    
    .big-num { font-size: 1.5rem; font-weight: bold; }
    .profit-text { color: #166534; font-weight: bold; }
    .loss-text { color: #991b1b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Momentum Sniper: Hit & Run Strategy")
st.markdown("**ระบบเทรดหุ้นซิ่ง: เน้นรอบจัด กำไร 10% / คัท 5% (ห้ามถือยาว!)**")
st.write("---")

# --- 2. รายชื่อหุ้นสายซิ่ง (High Beta / Growth) ---
RACING_STOCKS = [
    "DELTA.BK", "HANA.BK", "KCE.BK",  # อิเล็กทรอนิกส์ (วิ่งแรง)
    "JMT.BK", "JMART.BK", "SINGER.BK", # การเงินสายซิ่ง
    "GULF.BK", "EA.BK", "GPSC.BK",    # โรงไฟฟ้า
    "SCBSEMI" # กองทุนซิ่งตัวเดียวที่เรามี
]

FUNDS_MAP = {"SCBSEMI": "SMH"}

# --- 3. ฟังก์ชันคำนวณ (Momentum Indicators) ---
@st.cache_data(ttl=300) # Cache 5 นาทีพอ เพราะเล่นสั้น
def get_momentum_data(ticker):
    try:
        # Map กองทุน
        symbol = FUNDS_MAP.get(ticker, ticker)
        
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if len(df) < 50: return None
        
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # 1. EMA (เส้นค่าเฉลี่ยไว)
        df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean() # เส้นซิ่ง
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean() # เส้นเทรนด์
        
        # 2. RSI (แรงส่ง)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 3. MACD (จุดกลับตัว)
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        return df
    except: return None

# --- 4. Logic วิเคราะห์สัญญาณ (Trend Following) ---
def analyze_momentum(df):
    price = df['Close'].iloc[-1]
    ema10 = df['EMA10'].iloc[-1]
    ema50 = df['EMA50'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    macd = df['MACD'].iloc[-1]
    signal = df['Signal'].iloc[-1]
    
    status = "Wait"
    color = "white"
    
    # กฎของ Momentum: ซื้อตอนกำลังขึ้น ไม่ใช่ซื้อตอนถูก
    # 1. ราคาต้องยืนเหนือ EMA10 (แปลว่าซิ่งอยู่)
    # 2. MACD ตัดขึ้น หรือ ยืนเหนือศูนย์
    # 3. RSI ต้องไม่อืด (เกิน 50) แต่ไม่เวอร์ (เกิน 75)
    
    if price > ema10 and macd > signal and rsi > 50:
        if rsi < 75:
            status = "🚀 LUI (ลุย!)"
            color = "#dcfce7" # เขียว
        else:
            status = "🔥 HOT (ระวังดอย)"
            color = "#fef9c3" # เหลือง
    elif price < ema10:
        status = "💤 SLEEP (พักตัว)"
        color = "#f3f4f6"
    
    return price, rsi, macd, status, color

# --- 5. Dashboard ---
col_list, col_calc = st.columns([2, 1])

with col_list:
    st.subheader("🏎️ สนามประลองความเร็ว (Scanner)")
    
    data_list = []
    my_bar = st.progress(0)
    
    for i, ticker in enumerate(RACING_STOCKS):
        df = get_momentum_data(ticker)
        if df is not None:
            price, rsi, macd, status, col = analyze_momentum(df)
            
            data_list.append({
                "Symbol": ticker.replace(".BK", ""),
                "Price": price,
                "RSI": rsi,
                "MACD": macd,
                "Signal": status,
                "Color": col
            })
        my_bar.progress((i + 1) / len(RACING_STOCKS))
    
    my_bar.empty()
    
    if data_list:
        res_df = pd.DataFrame(data_list)
        
        def highlight_rows(row):
            return [f'background-color: {row["Color"]}; color: black'] * len(row)

        st.dataframe(
            res_df.style.apply(highlight_rows, axis=1).format({"Price": "{:,.2f}", "RSI": "{:.1f}", "MACD": "{:.2f}"}),
            column_order=["Symbol", "Price", "Signal", "RSI", "MACD"],
            height=500,
            use_container_width=True
        )

# --- 6. เครื่องคิดเลข 10/5 (Profit Hunter) ---
with col_calc:
    st.subheader("🧮 แผนเทรด (Trade Setup)")
    
    with st.container(border=True):
        st.info("💡 **กฎเหล็กวิศวกร:** เข้าเร็ว ออกไว ห้ามใจอ่อน")
        
        # เลือกหุ้นเพื่อดึงราคามาใส่ให้อัตโนมัติ
        stock_select = st.selectbox("เลือกหุ้นที่จะเล่น:", [d['Symbol'] for d in data_list] if data_list else [])
        
        current_p = 0.0
        if data_list:
            current_p = next((item['Price'] for item in data_list if item["Symbol"] == stock_select), 0.0)
        
        entry_price = st.number_input("ราคาเข้าซื้อ (บาท)", value=current_p, step=0.25)
        budget = st.number_input("เงินหน้าตัก (บาท)", value=10000, step=1000)
        
        if entry_price > 0:
            qty = int(budget / entry_price)
            
            # คำนวณเป้าหมาย (Fixed Rule: Profit 10% / Loss 5%)
            take_profit = entry_price * 1.10
            stop_loss = entry_price * 0.95
            
            profit_amt = (take_profit - entry_price) * qty
            loss_amt = (entry_price - stop_loss) * qty
            
            st.write("---")
            
            # แสดงแผนการเล่น
            st.markdown(f"""
            <div class="target-box">
                <div>จำนวนที่ซื้อได้: <b>{qty:,} หุ้น</b></div>
            </div>
            <br>
            <div class="bull-box">
                <div>🎯 <b>เป้าขาย (Take Profit): {take_profit:.2f}</b></div>
                <div class="profit-text">+10% (กำไร {profit_amt:,.0f} บาท)</div>
            </div>
            <br>
            <div class="bear-box">
                <div>🛑 <b>จุดหนี (Stop Loss): {stop_loss:.2f}</b></div>
                <div class="loss-text">-5% (ขาดทุน {loss_amt:,.0f} บาท)</div>
                <small>*หลุดราคานี้ต้องโยนซ้ายทันที ห้ามต่อรอง*</small>
            </div>
            """, unsafe_allow_html=True)

# --- 7. กราฟเทคนิค (Fast Mode) ---
st.write("---")
st.subheader(f"📈 กราฟความเร็วสูง: {stock_select}")

if stock_select:
    ticker_chart = next((t for t in RACING_STOCKS if t.replace(".BK", "") == stock_select), None)
    df_chart = get_momentum_data(ticker_chart)
    
    if df_chart is not None:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        
        # ราคา + EMA 10 (เส้นซิ่ง)
        fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                        low=df_chart['Low'], close=df_chart['Close'], name='Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA10'], name='EMA 10 (เส้นซิ่ง)', line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA50'], name='EMA 50 (เทรนด์)', line=dict(color='blue', width=2)), row=1, col=1)
        
        # MACD
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MACD'], name='MACD', line=dict(color='green')), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Signal'], name='Signal', line=dict(color='red', dash='dot')), row=2, col=1)
        fig.add_hline(y=0, line_dash="solid", line_color="gray", row=2, col=1)
        
        fig.update_layout(height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("💡 **ทริควิศวกร:** ถ้าเส้น EMA 10 (สีส้ม) ตัดขึ้นเหนือ EMA 50 (สีฟ้า) + MACD เขียว = **จุดพลุสัญญาณซิ่งครับ!** 🚀")
