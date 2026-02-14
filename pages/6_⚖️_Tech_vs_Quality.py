import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# --- Configuration ---
st.set_page_config(
    page_title="Fund Allocator: SCB vs KKP (RSI Strategy)",
    page_icon="⚖️",
    layout="wide"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main { background-color: #020617; }
    .stMetric {
        background-color: #0f172a;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #1e293b;
    }
    .fund-card {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 15px;
        border-top: 5px solid #2563eb;
        margin-bottom: 10px;
    }
    .highlight-kkp { border-top: 5px solid #8b5cf6; }
    .highlight-scb { border-top: 5px solid #2563eb; }
    .rsi-badge {
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- RSI Calculation Logic (FIXED FOR VALUE ERROR) ---
def calculate_rsi(ticker_symbol, window=14):
    try:
        # ดึงข้อมูล 1 เดือนเพื่อให้ได้ค่า RSI-14 ที่แม่นยำ
        data = yf.download(ticker_symbol, period="1mo", interval="1d", progress=False)
        if data.empty: return None, 0
        
        # จัดการกรณี yfinance คืนค่าเป็น DataFrame ที่มี MultiIndex
        if isinstance(data['Close'], pd.DataFrame):
            close = data['Close'].iloc[:, 0] # ดึงคอลัมน์แรกออกมาเป็น Series
        else:
            close = data['Close']
            
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        # ป้องกันการหารด้วยศูนย์
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        
        # ดึงเฉพาะค่าสุดท้ายออกมาเป็นตัวเลข (Float) เพื่อป้องกัน Error
        rsi_val = float(rsi_series.iloc[-1])
        
        curr_price = float(close.iloc[-1])
        prev_close = float(close.iloc[-2])
        change_pct = ((curr_price - prev_close) / prev_close) * 100
        
        if pd.isna(rsi_val): return None, 0
        
        return round(rsi_val, 2), round(change_pct, 2)
    except Exception as e:
        return None, 0

# --- Strategy Logic: Mapping RSI to Investment Weight ---
def get_suggested_weight(rsi):
    # ตรวจสอบว่า rsi เป็นตัวเลขตัวเดียวจริงๆ
    if rsi is None: return 50 
    try:
        rsi_float = float(rsi)
        if rsi_float < 30: return 100    # Oversold - ใส่เต็ม 100%
        if rsi_float < 40: return 80     # เริ่มถูก - เน้นเก็บ
        if rsi_float > 70: return 0      # Overbought - พักก่อน
        if rsi_float > 60: return 20     # เริ่มแพง - ทยอยหยุด
        return 50                  # ปกติ - DCA 50/50
    except:
        return 50

# --- Fund Database (9 Strategic Groups) ---
fund_map = {
    "S&P 500 (US)": {"ticker": "^GSPC", "scb": "SCBRMS&P500", "kkp": "KKP S&P500 SET-RMF", "desc": "หุ้นใหญ่สหรัฐฯ 500 ตัว"},
    "Nasdaq 100 (Tech)": {"ticker": "^NDX", "scb": "SCBNDQ", "kkp": "KKP NDQ100-H-RMF", "desc": "หุ้นเทคโนโลยีและนวัตกรรม"},
    "Global Quality": {"ticker": "QUAL", "scb": "SCBGQUAL", "kkp": "KKP GNP RMF-UH", "desc": "หุ้นโลกพื้นฐานแกร่ง (Active)"},
    "Semiconductor": {"ticker": "SOXX", "scb": "SCBSEMI", "kkp": "KKP TECH-H-RMF", "desc": "ชิปและโครงสร้างพื้นฐาน AI"},
    "China (H-Shares)": {"ticker": "ASHR", "scb": "SCBCE", "kkp": "KKP CHINA-H", "desc": "หุ้นจีนแผ่นดินใหญ่ (Value Play)"},
    "Vietnam (Growth)": {"ticker": "VNM", "scb": "SCBVIET", "kkp": "KKP VIETNAM-H", "desc": "หุ้นเวียดนาม ตลาดเกิดใหม่ยอดนิยม"},
    "Health Care": {"ticker": "XLV", "scb": "SCBGH", "kkp": "KKP GHC", "desc": "หุ้นสุขภาพ ทนทานต่อสภาวะเศรษฐกิจ"},
    "Gold (Safe Haven)": {"ticker": "GC=F", "scb": "SCBGOLD", "kkp": "KKP GOLD-H", "desc": "ทองคำเพื่อป้องกันความเสี่ยง"},
    "SET 50 (Thailand)": {"ticker": "^SET50.BK", "scb": "SCBSET50", "kkp": "KKP SET50", "desc": "หุ้นไทยขนาดใหญ่ 50 ตัว"}
}

# --- Header ---
st.title("⚖️ Smart Fund Allocator (RSI Strategy v2)")
st.caption("ระบบวิเคราะห์ความถูกแพงของตลาดโลก 9 กลุ่มยุทธศาสตร์ เพื่อจัดสรร RMF (SCB vs KKP)")

# --- Dashboard: Market Overview with RSI ---
st.subheader("📊 Market Strategy Dashboard (ภาพรวม 9 กลุ่ม)")
with st.spinner("กำลังเจาะข้อมูลตลาดโลก..."):
    market_stats = []
    for category, info in fund_map.items():
        rsi_val, change = calculate_rsi(info['ticker'])
        weight = get_suggested_weight(rsi_val)
        market_stats.append({
            "สินทรัพย์": category,
            "ดัชนีอ้างอิง": info['ticker'],
            "ราคาเปลี่ยนแปลง": f"{change:+.2f}%",
            "RSI (14 วัน)": rsi_val if rsi_val else "N/A",
            "KKP Weight (%)": f"{weight}%",
            "AI Action": "🔥 ใส่เต็ม (Buy)" if weight >= 80 else "🛡️ พักเงิน (Wait)" if weight <= 20 else "📈 DCA ปกติ"
        })

    df_market = pd.DataFrame(market_stats)
    st.dataframe(df_market, use_container_width=True, hide_index=True)

st.divider()

# --- Section: Interactive Allocator ---
col_sel, col_bud = st.columns([2, 1])
with col_sel:
    selected_cat = st.selectbox("เลือกกลุ่มที่ต้องการจัดสรรเงินรอบนี้", list(fund_map.keys()))
with col_bud:
    budget = st.number_input("งบประมาณลงทุน (บาท)", min_value=0, value=10000, step=1000)

current_info = fund_map[selected_cat]
curr_rsi, curr_change = calculate_rsi(current_info['ticker'])
ai_suggested_kkp = get_suggested_weight(curr_rsi)

# --- Allocation UI ---
st.write(f"### 🎯 กลยุทธ์สำหรับ {selected_cat}")
st.markdown(f"**รายละเอียด:** {current_info['desc']} | **RSI ปัจจุบัน:** {curr_rsi}")

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""<div class="fund-card highlight-scb">
        <h3 style='color:#60a5fa;'>💜 SCB AM</h3>
        <p style='font-size:1.2rem; font-weight:bold;'>{current_info['scb']}</p>
        <p style='color:#94a3b8; font-size:0.9rem;'>เน้นความเรียบง่าย / ค่าธรรมเนียมต่ำ</p>
    </div>""", unsafe_allow_html=True)
    
    # Slider ปรับน้ำหนักตาม AI แนะนำเป็นค่าเริ่มต้น
    scb_weight = st.slider("สัดส่วน SCB (%)", 0, 100, int(100 - ai_suggested_kkp))

with c2:
    st.markdown(f"""<div class="fund-card highlight-kkp">
        <h3 style='color:#a78bfa;'>🧡 KKP AM</h3>
        <p style='font-size:1.2rem; font-weight:bold;'>{current_info['kkp']}</p>
        <p style='color:#94a3b8; font-size:0.9rem;'>เน้นบริหารเชิงรุก / ป้องกันความเสี่ยง</p>
    </div>""", unsafe_allow_html=True)
    
    kkp_weight = 100 - scb_weight
    st.metric("สัดส่วน KKP", f"{kkp_weight}%", delta=f"AI แนะนำ: {ai_suggested_kkp}%")

st.divider()

# --- Result Summary ---
r1, r2, r3 = st.columns(3)
scb_amt = budget * (scb_weight / 100)
kkp_amt = budget * (kkp_weight / 100)

with r1:
    st.metric("ลงทุน SCB", f"฿{scb_amt:,.2f}")
with r2:
    st.metric("ลงทุน KKP", f"฿{kkp_amt:,.2f}")
with r3:
    if kkp_weight >= 80:
        st.success("🚀 STRATEGY: STRONG BUY")
    elif kkp_weight <= 20:
        st.warning("🛡️ STRATEGY: HOLD / CASH")
    else:
        st.info("📈 STRATEGY: DCA MODE")

# --- Strategy Analysis ---
st.write("### 🧠 AI Strategy Analysis")
if curr_rsi:
    if curr_rsi < 30:
        st.success(f"**จังหวะทอง:** RSI อยู่ที่ {curr_rsi} (Oversold) ตลาดกลัวเกินเหตุ เป็นจังหวะเข้าทำกำไรระยะยาวที่ดีที่สุด")
    elif curr_rsi > 70:
        st.error(f"**จังหวะระวัง:** RSI อยู่ที่ {curr_rsi} (Overbought) ตลาดร้อนแรงเกินไป มีความเสี่ยงที่จะพักฐาน")
    else:
        st.info(f"**จังหวะปกติ:** RSI {curr_rsi} ตลาดทรงตัว แนะนำแบ่งเงินลงทุนตามวินัย eDCA")

st.divider()
st.caption(f"ข้อมูล Real-time อ้างอิง Ticker ตลาดโลก | Last Update: {datetime.now().strftime('%H:%M:%S')}")
