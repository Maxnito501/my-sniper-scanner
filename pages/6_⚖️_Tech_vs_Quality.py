import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# --- Configuration ---
st.set_page_config(
    page_title="Fund Allocator: SCB vs KKP (Premium Edition)",
    page_icon="⚖️",
    layout="wide"
)

# --- Custom Styling (Premium Light Theme) ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #f1f5f9;
    }
    
    /* Global Text Color */
    .main .block-container {
        color: #1e293b;
    }

    /* Metric Styling */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
    }

    /* Fund Card Styling */
    .fund-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 20px;
        margin-bottom: 15px;
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s;
    }
    .fund-card:hover {
        transform: translateY(-5px);
    }

    /* Highlight Borders */
    .highlight-scb { border-left: 8px solid #6366f1; }
    .highlight-kkp { border-left: 8px solid #f59e0b; }

    /* Titles */
    h1, h2, h3 {
        color: #0f172a !important;
        font-weight: 800 !important;
    }
    
    /* Info/Success Boxes */
    .stAlert {
        border-radius: 12px;
    }
    
    /* Slider Styling */
    .stSlider > div [data-baseweb="slider"] {
        margin-top: 20px;
    }

    /* Strategy Note Box */
    .strategy-box {
        background-color: #f8fafc;
        padding: 15px;
        border-radius: 12px;
        border: 1px dashed #cbd5e1;
    }
    </style>
    """, unsafe_allow_html=True)

# --- RSI Calculation Logic (Robust Scalar Version) ---
def calculate_rsi(ticker_symbol, window=14):
    try:
        data = yf.download(ticker_symbol, period="1mo", interval="1d", progress=False)
        if data.empty: return None, 0
        
        if isinstance(data['Close'], pd.DataFrame):
            close = data['Close'].iloc[:, 0]
        else:
            close = data['Close']
            
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        
        rsi_val = float(rsi_series.iloc[-1])
        curr_price = float(close.iloc[-1])
        prev_close = float(close.iloc[-2])
        change_pct = ((curr_price - prev_close) / prev_close) * 100
        
        if pd.isna(rsi_val): return None, 0
        return round(rsi_val, 2), round(change_pct, 2)
    except:
        return None, 0

# --- Strategy Logic ---
def get_suggested_weight(rsi):
    if rsi is None: return 50 
    try:
        rsi_float = float(rsi)
        if rsi_float < 35: return 100    # Oversold
        if rsi_float < 45: return 80     # Cheap
        if rsi_float > 65: return 0      # Overbought
        if rsi_float > 55: return 20     # Getting Expensive
        return 50                        # Neutral
    except:
        return 50

# --- Fund Database (9 Groups) ---
fund_map = {
    "S&P 500 (US)": {"ticker": "^GSPC", "scb": "SCBRMS&P500", "kkp": "KKP S&P500 SET-RMF", "desc": "หุ้นใหญ่สหรัฐฯ 500 ตัว"},
    "Nasdaq 100 (Tech)": {"ticker": "^NDX", "scb": "SCBNDQ", "kkp": "KKP NDQ100-H-RMF", "desc": "หุ้นเทคโนโลยีระดับโลก"},
    "Global Quality": {"ticker": "QUAL", "scb": "SCBGQUAL", "kkp": "KKP GNP RMF-UH", "desc": "หุ้นโลกพื้นฐานแกร่ง (Active)"},
    "Semiconductor": {"ticker": "SOXX", "scb": "SCBSEMI", "kkp": "KKP TECH-H-RMF", "desc": "ชิปและ AI Infrastructure"},
    "China (H-Shares)": {"ticker": "ASHR", "scb": "SCBCE", "kkp": "KKP CHINA-H", "desc": "หุ้นจีน (Value Opportunity)"},
    "Vietnam (Growth)": {"ticker": "VNM", "scb": "SCBVIET", "kkp": "KKP VIETNAM-H", "desc": "หุ้นเวียดนาม ตลาดเกิดใหม่"},
    "Health Care": {"ticker": "XLV", "scb": "SCBGH", "kkp": "KKP GHC", "desc": "หุ้นสุขภาพ (Defensive)"},
    "Gold (Safe Haven)": {"ticker": "GC=F", "scb": "SCBGOLD", "kkp": "KKP GOLD-H", "desc": "ทองคำเพื่อลดความเสี่ยง"},
    "SET 50 (Thailand)": {"ticker": "^SET50.BK", "scb": "SCBSET50", "kkp": "KKP SET50", "desc": "หุ้นไทยขนาดใหญ่ 50 ตัว"}
}

# --- Header Section ---
st.title("⚖️ Smart Fund Allocator")
st.markdown("### 🗺️ AI Strategy Dashboard (eDCA)")
st.caption(f"อัปเดตจังหวะการลงทุนตลาดโลก: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- Metrics Row ---
with st.spinner("กำลังเจาะข้อมูลตลาด..."):
    m1, m2, m3, m4 = st.columns(4)
    spx_rsi, spx_chg = calculate_rsi("^GSPC")
    ndq_rsi, ndq_chg = calculate_rsi("^NDX")
    gold_rsi, gold_chg = calculate_rsi("GC=F")
    set_rsi, set_chg = calculate_rsi("^SET50.BK")
    
    m1.metric("S&P 500 RSI", f"{spx_rsi}", f"{spx_chg}%")
    m2.metric("Nasdaq RSI", f"{ndq_rsi}", f"{ndq_chg}%")
    m3.metric("Gold RSI", f"{gold_rsi}", f"{gold_chg}%")
    m4.metric("SET 50 RSI", f"{set_rsi}", f"{set_chg}%")

st.divider()

# --- Main Dashboard Table ---
st.subheader("📊 ภาพรวม 9 กลุ่มยุทธศาสตร์")
market_stats = []
for category, info in fund_map.items():
    rsi_val, change = calculate_rsi(info['ticker'])
    weight = get_suggested_weight(rsi_val)
    market_stats.append({
        "กลุ่มสินทรัพย์": category,
        "RSI (14)": rsi_val if rsi_val else "N/A",
        "เปลี่ยนแปลง": f"{change:+.2f}%",
        "KKP Weight (%)": f"{weight}%",
        "AI Recommendation": "🔥 ใส่เต็ม (Strong Buy)" if weight >= 80 else "🛡️ พักเงิน (Wait)" if weight <= 20 else "📈 DCA ปกติ"
    })
st.dataframe(pd.DataFrame(market_stats), use_container_width=True, hide_index=True)

st.divider()

# --- Interactive Allocation Section ---
st.subheader("🎯 ปรับสัดส่วนการลงทุนรายรอบ")
col_config, col_space = st.columns([1, 1])

with col_config:
    selected_cat = st.selectbox("เลือกกลุ่มกองทุนที่ต้องการจัดสรร", list(fund_map.keys()))
    budget = st.number_input("ยอดเงินลงทุนรอบนี้ (บาท)", min_value=0, value=10000, step=1000)

current_info = fund_map[selected_cat]
curr_rsi, curr_change = calculate_rsi(current_info['ticker'])
ai_suggested_kkp = get_suggested_weight(curr_rsi)

# Layout for Fund Cards
c_scb, c_kkp = st.columns(2)

with c_scb:
    st.markdown(f"""<div class="fund-card highlight-scb">
        <p style='color:#4f46e5; font-size:0.8rem; font-weight:bold; margin-bottom:5px;'>SCB ASSET MANAGEMENT</p>
        <h2 style='margin-top:0;'>{current_info['scb']}</h2>
        <p style='color:#64748b; font-size:0.9rem;'>{current_info['desc']}</p>
        <p style='color:#334155; font-size:0.85rem; font-style:italic;'>เน้นความเรียบง่ายและค่าธรรมเนียมต่ำ</p>
    </div>""", unsafe_allow_html=True)
    
    scb_weight = st.slider("ระบุสัดส่วน SCB (%)", 0, 100, int(100 - ai_suggested_kkp))

with c_kkp:
    st.markdown(f"""<div class="fund-card highlight-kkp">
        <p style='color:#d97706; font-size:0.8rem; font-weight:bold; margin-bottom:5px;'>KKP ASSET MANAGEMENT</p>
        <h2 style='margin-top:0;'>{current_info['kkp']}</h2>
        <p style='color:#64748b; font-size:0.9rem;'>{current_info['desc']}</p>
        <p style='color:#334155; font-size:0.85rem; font-style:italic;'>เน้นบริหารเชิงรุก / ป้องกันความเสี่ยง</p>
    </div>""", unsafe_allow_html=True)
    
    kkp_weight = 100 - scb_weight
    st.metric("สัดส่วน KKP ที่แนะนำ", f"{kkp_weight}%", delta=f"AI แนะนำ: {ai_suggested_kkp}%")

# --- Allocation Results ---
st.divider()
r1, r2, r3 = st.columns(3)
scb_amt = budget * (scb_weight / 100)
kkp_amt = budget * (kkp_weight / 100)

with r1:
    st.metric("เงินลงทุน SCB", f"฿{scb_amt:,.2f}")
with r2:
    st.metric("เงินลงทุน KKP", f"฿{kkp_amt:,.2f}")
with r3:
    st.markdown("<div class='strategy-box'>", unsafe_allow_html=True)
    if kkp_weight >= 80:
        st.success("🎯 **STRATEGY: STRONG BUY**")
        st.caption("จังหวะ RSI ต่ำ คือโอกาสทอง")
    elif kkp_weight <= 20:
        st.warning("🛡️ **STRATEGY: CAUTION**")
        st.caption("ตลาดร้อนแรงเกินไป เน้นถือเงินสด")
    else:
        st.info("📈 **STRATEGY: STEADY DCA**")
        st.caption("ลงทุนตามวินัยรายรอบปกติ")
    st.markdown("</div>", unsafe_allow_html=True)

# --- AI Commentary ---
if curr_rsi:
    with st.expander("🔍 AI Market Analysis & Commentary"):
        if curr_rsi < 35:
            st.write(f"วิศวกรโบ้ครับ! ค่า RSI ของ {selected_cat} อยู่ที่ **{curr_rsi}** ซึ่งเข้าเขต Oversold อย่างชัดเจน ตลาดกำลังอยู่ในจุดที่กลัวเกินเหตุ นี่คือจังหวะที่ควรดึงงบ eDCA มาใส่เต็มร้อย (100%) เพื่อผลตอบแทนในอนาคตครับ")
        elif curr_rsi > 65:
            st.write(f"ค่า RSI ของ {selected_cat} อยู่ที่ **{curr_rsi}** ซึ่งค่อนข้างแพง (Overbought) ตลาดกำลังไล่ราคากันอย่างรุนแรง แนะนำให้หยุดเติมเงินเพิ่ม หรือขยับน้ำหนักไปถือเงินสด 0% รอการพักฐานครับ")
        else:
            st.write(f"สภาวะตลาดของ {selected_cat} อยู่ในโซนปกติ (RSI: {curr_rsi}) แนะนำแบ่งสัดส่วนตามยุทธศาสตร์ 50/50 เพื่อรักษาวินัยการลงทุนครับ")

st.divider()
st.caption("ออกแบบโดยวิศวกร เพื่อวิศวกร • ข้อมูล Ticker เรียลไทม์จาก Yahoo Finance")
