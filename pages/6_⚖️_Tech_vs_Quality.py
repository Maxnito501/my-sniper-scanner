import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# --- Configuration ---
st.set_page_config(
    page_title="Fund Sniper: SCB vs KKP Battle",
    page_icon="⚖️",
    layout="wide"
)

# --- Custom Styling (Professional Light Theme) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
    }
    .fund-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
    }
    .scb-line { border-left: 6px solid #6366f1; }
    .kkp-line { border-left: 6px solid #f59e0b; }
    h1, h2, h3 { color: #0f172a !important; }
    .stAlert { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- RSI Calculation Logic ---
def get_live_rsi(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if data.empty: return None, 0
        close = data['Close'].iloc[:, 0] if isinstance(data['Close'], pd.DataFrame) else data['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        change = ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100
        return round(float(rsi.iloc[-1]), 2), round(float(change), 2)
    except:
        return None, 0

# --- Strategy Pairs Database (4 Key Pairs) ---
strategic_pairs = {
    "S&P 500 (ตลาดสหรัฐฯ)": {
        "ticker": "^GSPC",
        "scb": "SCBRMS&P500",
        "kkp": "KKP S&P500 SET-RMF",
        "desc": "ดัชนีหุ้นใหญ่ 500 ตัวของสหรัฐฯ"
    },
    "Nasdaq 100 (หุ้นเทค)": {
        "ticker": "^NDX",
        "scb": "SCBNDQ",
        "kkp": "KKP NDQ100-H-RMF",
        "desc": "หุ้นนวัตกรรมและเทคโนโลยีระดับโลก"
    },
    "Global Quality (หุ้นคุณภาพ)": {
        "ticker": "QUAL",
        "scb": "SCBGQUAL",
        "kkp": "KKP GNP RMF-UH",
        "desc": "คัดหุ้นผู้ชนะที่มีพื้นฐานแกร่งทั่วโลก"
    },
    "Semiconductor (ชิป & AI)": {
        "ticker": "SOXX",
        "scb": "SCBSEMI",
        "kkp": "KKP TECH-H-RMF",
        "desc": "หัวใจของ AI และเทคโนโลยีแห่งอนาคต"
    }
}

# --- Header ---
st.title("⚖️ Fund Sniper Battle Matrix")
st.caption(f"ระบบเปรียบเทียบยุทธศาสตร์ SCB vs KKP (เรียลไทม์) | {datetime.now().strftime('%H:%M:%S')}")

# --- Market Overview Table ---
st.subheader("📊 ตารางวิเคราะห์จังหวะเข้าทำ (RSI Scan)")
with st.spinner("กำลังเจาะข้อมูลตลาดโลก..."):
    summary_data = []
    for name, info in strategic_pairs.items():
        rsi, chg = get_live_rsi(info['ticker'])
        # Decision Logic
        if rsi and rsi < 40: action = "🔥 น่าช้อน (Strong Buy)"
        elif rsi and rsi > 60: action = "🛡️ พักเงิน (Wait)"
        else: action = "📈 DCA ปกติ"
        
        summary_data.append({
            "กลุ่มสินทรัพย์": name,
            "RSI (14)": rsi if rsi else "N/A",
            "Change (%)": f"{chg:+.2f}%",
            "AI Suggestion": action,
            "Strategy": "เน้น KKP" if rsi and rsi < 45 else "เน้น SCB"
        })
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

st.divider()

# --- Interactive Battle Zone ---
st.subheader("🎯 เจาะลึกรายคู่และจัดสรรยอดเงิน")
selected_pair = st.selectbox("เลือกคู่ยุทธศาสตร์ที่ต้องการลงทุน", list(strategic_pairs.keys()))
budget = st.number_input("ยอดเงินลงทุนรอบนี้ (บาท)", value=10000, step=1000)

info = strategic_pairs[selected_pair]
rsi_val, _ = get_live_rsi(info['ticker'])

# AI Suggestion Logic for Slider
default_kkp = 100 if rsi_val and rsi_val < 35 else 80 if rsi_val and rsi_val < 45 else 50 if rsi_val and rsi_val < 60 else 0

col_cards, col_res = st.columns([2, 1])

with col_cards:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="fund-card scb-line">
            <p style='color:#6366f1; font-weight:bold; font-size:0.8rem;'>SCB AM</p>
            <h4 style='margin:0;'>{info['scb']}</h4>
            <p style='color:#64748b; font-size:0.8rem;'>เน้นประหยัด / ค่าฟีต่ำ</p>
        </div>""", unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""<div class="fund-card kkp-line">
            <p style='color:#f59e0b; font-weight:bold; font-size:0.8rem;'>KKP AM</p>
            <h4 style='margin:0;'>{info['kkp']}</h4>
            <p style='color:#64748b; font-size:0.8rem;'>เน้นบริหารเชิงรุก / Dime!</p>
        </div>""", unsafe_allow_html=True)
    
    kkp_weight = st.slider(f"ปรับสัดส่วน KKP สำหรับ {selected_pair} (%)", 0, 100, int(default_kkp))
    scb_weight = 100 - kkp_weight

with col_res:
    st.metric("RSI ปัจจุบัน", f"{rsi_val}")
    st.write("---")
    st.metric(f"ลง SCB ({scb_weight}%)", f"฿{budget * (scb_weight/100):,.2f}")
    st.metric(f"ลง KKP ({kkp_weight}%)", f"฿{budget * (kkp_weight/100):,.2f}")

if rsi_val:
    if rsi_val < 40:
        st.success(f"💡 **วิเคราะห์:** RSI ต่ำ ({rsi_val}) ตลาดเริ่มถูก พี่โบ้ควรเน้นไปที่ **{info['kkp']}** เพื่อรับแรงดีดกลับครับ")
    elif rsi_val > 60:
        st.warning(f"💡 **วิเคราะห์:** ตลาดเริ่มแพง (RSI {rsi_val}) แนะนำถือเงินสดรับดอกเบี้ย 3% ใน Dime! รอไปก่อนครับ")
    else:
        st.info("💡 **วิเคราะห์:** ตลาดปกติ แนะนำแบ่งสัดส่วน 50/50 เพื่อวินัยการลงทุน")

st.divider()
st.caption("Suchat Engineering Trading System • ข้อมูล Ticker เรียลไทม์ (Delay 15m)")
