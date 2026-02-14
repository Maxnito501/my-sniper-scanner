import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# --- Configuration ---
st.set_page_config(
    page_title="Fund Allocator: SCB vs KKP",
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
    .market-status {
        font-size: 0.8rem;
        color: #94a3b8;
        font-style: italic;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Real-time Market Data Logic ---
@st.cache_data(ttl=300)
def get_market_sentiment(ticker):
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1d", interval="5m")
        if not hist.empty:
            curr_price = hist['Close'].iloc[-1]
            prev_close = data.info.get('previousClose', curr_price)
            change = ((curr_price - prev_close) / prev_close) * 100
            return curr_price, change
    except:
        return None, 0
    return None, 0

# --- Fund Database (Mapped with Real-time Tickers) ---
fund_data = {
    "S&P 500 (หุ้นสหรัฐฯ)": {
        "ticker": "^GSPC",
        "scb": {"name": "SCBRMS&P500", "focus": "ค่าธรรมเนียมต่ำมาก", "type": "Index Fund"},
        "kkp": {"name": "KKP S&P500 SET-RMF", "focus": "ความประหยัดสูงสุด", "type": "Index Fund"},
        "strategy": "เน้นถือยาวตามดัชนีเศรษฐกิจสหรัฐฯ"
    },
    "Nasdaq 100 (หุ้นเทคโนโลยี)": {
        "ticker": "^NDX",
        "scb": {"name": "SCBNDQ", "focus": "ดัชนีเทค Nasdaq", "type": "Index Fund"},
        "kkp": {"name": "KKP NDQ100-H-RMF", "focus": "Hedged ค่าเงินเสถียร", "type": "Index Fund"},
        "strategy": "เน้นเติบโตไปกับนวัตกรรมและ AI"
    },
    "Global Quality (หุ้นโลกผู้ชนะ)": {
        "ticker": "QUAL",
        "scb": {"name": "SCBGQUAL", "focus": "หุ้นคุณภาพพื้นฐานแกร่ง", "type": "Passive/Factor"},
        "kkp": {"name": "KKP GNP RMF-UH", "focus": "Active (Capital Group) คัดผู้ชนะ", "type": "Active Fund"},
        "strategy": "เน้นความผันผวนต่ำโดยผู้เชี่ยวชาญเลือกหุ้น"
    },
    "Tech & Semiconductor (เทคเฉพาะทาง)": {
        "ticker": "SOXX",
        "scb": {"name": "SCBSEMI", "focus": "เน้นกลุ่ม Chip", "type": "Sector Fund"},
        "kkp": {"name": "KKP TECH-H-RMF", "focus": "เน้น Software และ AI Service", "type": "Sector Fund"},
        "strategy": "เน้นโครงสร้างพื้นฐานของระบบ AI โลก"
    }
}

# --- Header ---
st.title("⚖️ Smart Fund Allocator (Real-time eDCA)")
st.caption("ระบบวิเคราะห์จังหวะตลาดโลกเพื่อจัดสรร RMF (SCB vs KKP) สำหรับวิศวกรโบ้")

# --- Selection & Input ---
with st.sidebar:
    st.header("🎯 ยุทธศาสตร์การจัดสรร")
    category = st.selectbox("เลือกกลุ่มสินทรัพย์", list(fund_data.keys()))
    total_budget = st.number_input("งบประมาณลงทุนรอบนี้ (บาท)", min_value=0, value=10000, step=1000)
    
    if st.button("🔄 อัปเดตราคาตลาดโลกสด"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    st.write("📈 **หลักการ eDCA คืนนี้:**")
    st.info("ใช้ราคาดัชนีตลาดโลก (Ticker) เป็นตัวนำทาง NAV กองทุนไทยที่จะประกาศตอนเย็น")

selected_asset = fund_data[category]
market_price, market_change = get_market_sentiment(selected_asset['ticker'])

# --- Market Sentiment Header ---
st.markdown(f"<p class='market-status'>ดัชนีอ้างอิง: {selected_asset['ticker']} | อัปเดตล่าสุด: {datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

m_col1, m_col2 = st.columns([1, 2])
with m_col1:
    if market_price:
        st.metric(f"สถานะ {selected_asset['ticker']}", f"{market_price:,.2f}", f"{market_change:.2f}%")
    else:
        st.warning("รอตลาดเปิด/กำลังดึงข้อมูล...")

with m_col2:
    if market_change < -1.0:
        st.error(f"⚠️ ตลาดลงหนัก ({market_change:.2f}%) จังหวะนี้ควรเน้นสะสมตัวที่ Underperform หรือ Active Fund")
    elif market_change > 1.0:
        st.success(f"🚀 ตลาดแรง ({market_change:.2f}%) พิจารณา DCA ตามวินัยในกองทุนดัชนี")
    else:
        st.info("📉 ตลาดแกว่งตัวแคบ เน้นจัดสรรตามสัดส่วนยุทธศาสตร์หลัก")

st.divider()

# --- Main Layout ---
col_scb, col_kkp = st.columns(2)

with col_scb:
    st.markdown(f"""<div class="fund-card highlight-scb">
        <h3 style='color:#60a5fa;'>💜 SCB AM</h3>
        <p style='font-size:1.2rem; font-weight:bold;'>{selected_asset['scb']['name']}</p>
        <p style='color:#94a3b8; font-size:0.9rem;'>{selected_asset['scb']['focus']}</p>
        <p style='color:#cbd5e1;'>ประเภท: {selected_asset['scb']['type']}</p>
    </div>""", unsafe_allow_html=True)
    
    # ออโต้แนะนำสัดส่วนเบื้องต้นตามสถานะตลาด
    default_scb = 40 if market_change < -0.5 else 50
    scb_weight = st.slider(f"สัดส่วนของ {selected_asset['scb']['name']} (%)", 0, 100, default_scb, key="scb_s")

with col_kkp:
    st.markdown(f"""<div class="fund-card highlight-kkp">
        <h3 style='color:#a78bfa;'>🧡 KKP AM (Stronger Pick)</h3>
        <p style='font-size:1.2rem; font-weight:bold;'>{selected_asset['kkp']['name']}</p>
        <p style='color:#94a3b8; font-size:0.9rem;'>{selected_asset['kkp']['focus']}</p>
        <p style='color:#cbd5e1;'>ประเภท: {selected_asset['kkp']['type']}</p>
    </div>""", unsafe_allow_html=True)
    
    kkp_weight = 100 - scb_weight
    st.write("") # Spacer
    st.metric(f"สัดส่วนของ {selected_asset['kkp']['name']}", f"{kkp_weight}%")

st.divider()

# --- Allocation Result ---
res_col1, res_col2, res_col3 = st.columns(3)

scb_amount = total_budget * (scb_weight / 100)
kkp_amount = total_budget * (kkp_weight / 100)

with res_col1:
    st.metric("เงินลงทุนฝั่ง SCB", f"฿{scb_amount:,.2f}")
with res_col2:
    st.metric("เงินลงทุนฝั่ง KKP", f"฿{kkp_amount:,.2f}", delta=f"{kkp_weight-50}% Weight" if kkp_weight!=50 else None)
with res_col3:
    st.markdown(f"""
    <div style='background-color:#0f172a; padding:15px; border-radius:10px; border:1px solid #334155;'>
        <p style='margin:0; font-size:0.8rem; color:#94a3b8;'>STRATEGY NOTE</p>
        <p style='margin:0; font-size:0.9rem; font-weight:bold;'>{selected_asset['strategy']}</p>
    </div>
    """, unsafe_allow_html=True)

# --- Summary & Action ---
st.write("### 📝 แผนการทำ eDCA วันนี้")
st.success(f"สรุปยอดลงทุน: **SCB ฿{scb_amount:,.2f}** | **KKP ฿{kkp_amount:,.2f}**")

# อัลกอริทึมแนะนำการตัดสินใจ
if category == "Global Quality (หุ้นโลกผู้ชนะ)" and market_change < -0.5:
    st.warning(f"💡 ตลาดพักตัว: แนะนำเน้นไปที่ **KKP GNP RMF-UH** เพราะเป็น Active Fund ทีมงาน Capital Group จะช่วยคัดหุ้นที่แข็งแกร่งในช่วงขาลงได้ดีกว่า")
elif kkp_weight > 50:
    st.info(f"💡 คุณกำลังให้น้ำหนักกับ **KKP** มากขึ้น เพื่อใช้ประโยชน์จาก {selected_asset['kkp']['focus']}")

st.divider()
st.caption("ระบบวางแผนยุทธศาสตร์กองทุน • ข้อมูล Real-time อ้างอิงจากตลาดโลก (Yahoo Finance API)")
