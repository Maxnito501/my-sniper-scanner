import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V2", page_icon="🧭", layout="wide")

st.title("🧭 Polaris: Strategic Investment Navigator")
st.markdown("""
**ระบบวิเคราะห์กลยุทธ์ลงทุนฉบับวิศวกร (Trend + Momentum)**
* **ถือยาว (Run Trend):** เมื่อราคายืนเหนือเส้นค่าเฉลี่ย 200 วัน (Bull Market)
* **เล่นสั้น (Swing Trade):** เมื่อราคาต่ำกว่าเส้น 200 วัน (Bear Market)
* **Action:** แนะนำจังหวะ ซื้อ / ถือ / ขาย ตาม RSI
""")
st.write("---")

# --- 2. ข้อมูลหุ้นและกองทุน (ชุดเดิม) ---
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
    "Gold (ทองคำโลก)": "GLD"
}

# --- 3. ฟังก์ชันคำนวณอินดิเคเตอร์ ---
def get_technical_data(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        if len(df) < 200: return None # ข้อมูลน้อยไปวิเคราะห์ไม่ได้

        # คำนวณ EMA (Trend)
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

        # คำนวณ RSI (Momentum)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        return df
    except:
        return None

# --- 4. ฟังก์ชันวิเคราะห์กลยุทธ์ (หัวใจสำคัญ) ---
def analyze_strategy(df):
    current_price = df['Close'].iloc[-1]
    ema200 = df['EMA200'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    
    # 1. วิเคราะห์แนวโน้ม (Trend)
    trend = "ขาขึ้น (Uptrend) 🐂" if current_price > ema200 else "ขาลง (Downtrend) 🐻"
    
    # 2. กำหนดกลยุทธ์ (Strategy)
    if current_price > ema200:
        strategy = "🟢 ถือยาว (Run Trend)"
        note = "ตลาดกระทิง เน้นถือทนรวย"
    else:
        strategy = "🔴 เล่นสั้น (Swing Trade)"
        note = "ตลาดหมี เด้งขาย-ย่อซื้อ"

    # 3. คำแนะนำการกระทำ (Action)
    action = "⏳ รอ (Wait)"
    color = "gray"
    
    if rsi <= 30:
        action = "🛒 ซื้อสะสม (Buy Dip)"
        color = "green"
    elif rsi >= 70:
        action = "💰 ขายทำกำไร (Take Profit)"
        color = "red"
    elif 30 < rsi < 45 and current_price > ema200:
        action = "➕ ซื้อเพิ่ม (Add More)" # ย่อตัวในขาขึ้น
        color = "lightgreen"
    
    return current_price, rsi, trend, strategy, action, color

# --- 5. แสดงผลแบบตารางสรุป (Dashboard) ---
st.subheader("📊 สรุปสถานะตลาด (Market Overview)")

data_list = []
# รวมรายการหุ้นและกองทุน
all_tickers = [(s, s) for s in STOCKS] + [(n, t) for n, t in FUNDS.items()]

progress_bar = st.progress(0)
for i, (name, ticker) in enumerate(all_tickers):
    df = get_technical_data(ticker)
    if df is not None:
        price, rsi, trend, strat, act, col = analyze_strategy(df)
        data_list.append({
            "Symbol": name.replace(".BK", ""),
            "Price": f"{price:,.2f}",
            "RSI": f"{rsi:.1f}",
            "Trend": trend,
            "Strategy": strat,
            "Action": act
        })
    progress_bar.progress((i + 1) / len(all_tickers))

progress_bar.empty()

# แปลงเป็น DataFrame และแสดงผล
res_df = pd.DataFrame(data_list)
st.dataframe(
    res_df.style.map(lambda x: 'color: green; font-weight: bold;' if 'ซื้อ' in str(x) else ('color: red; font-weight: bold;' if 'ขาย' in str(x) else ''), subset=['Action']),
    height=600, 
    use_container_width=True
)

# --- 6. ส่วนเจาะลึกรายตัว ---
st.write("---")
st.subheader("🔍 เจาะลึกรายตัว (Deep Dive)")
selected_item = st.selectbox("เลือกดูรายละเอียดกราฟ", [x['Symbol'] for x in data_list])

# หากราฟของตัวที่เลือก
target_ticker = next((t for n, t in all_tickers if n.replace(".BK", "") == selected_item), None)

if target_ticker:
    df = get_technical_data(target_ticker)
    if df is not None:
        # สร้างกราฟ Plotly
        fig = go.Figure()
        
        # ราคา & EMA
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price', line=dict(color='black')))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA 50 (กลาง)', line=dict(color='orange', width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200 (ยาว)', line=dict(color='blue', width=2)))
        
        fig.update_layout(title=f"Technical Chart: {selected_item}", height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # คำอธิบาย
        st.info(f"""
        **ความหมายเส้น:**
        * **เส้นสีดำ (ราคา):** ถ้าอยู่เหนือเส้นน้ำเงิน = ขาขึ้น (Bullish)
        * **เส้นสีน้ำเงิน (EMA 200):** เส้นแบ่งนรก-สวรรค์ (ตัวบอกเทรนด์ระยะยาว)
        * **เส้นสีส้ม (EMA 50):** แนวรับ-แนวต้าน ระยะกลาง
        """)
