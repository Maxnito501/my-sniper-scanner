import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# --- Configuration ---
st.set_page_config(
    page_title="Fund Sniper: RMF Battle (SCB vs KKP)",
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
    h1, h2, h3 { color: #0f172a !important; font-family: 'Kanit', sans-serif; }
    .stAlert { border-radius: 12px; }
    .strategy-note {
        background-color: #f1f5f9;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #334155;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- RSI Calculation Logic (Protected for Real-time) ---
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

# --- Strategy Pairs Database (Focus on RMF) ---
strategic_pairs = {
    "S&P 500 (RMF)": {
        "ticker": "^GSPC",
        "scb": "SCBRMS&P500",
        "kkp": "KKP S&P500 SET-RMF",
        "desc": "หุ้นใหญ่สหรัฐฯ 500 ตัว เพื่อการเกษียณ"
    },
    "Nasdaq 100 (RMF)": {
        "ticker": "^NDX",
        "scb": "SCBNDQ(RMF)",
        "kkp": "KKP NDQ100-H-RMF",
        "desc": "หุ้นเทคโนโลยีระดับโลก พร้อมสิทธิภาษี"
    },
    "Global Quality (RMF)": {
        "ticker": "QUAL",
        "scb": "SCBGQUAL-RMF",
        "kkp": "KKP GNP RMF-UH",
        "desc": "หุ้นโลกพื้นฐานแกร่ง คัดโดยผู้เชี่ยวชาญ"
    },
    "Semiconductor (RMF)": {
        "ticker": "SOXX",
        "scb": "SCBSEMI(RMF)",
        "kkp": "KKP TECH-H-RMF",
        "desc": "กลุ่มชิปและ AI (KKP จะกระจายกลุ่ม Software ด้วย)"
    }
}

# --- Extended Monitoring (For Dip Buying / ช้อนเก็บ) ---
extended_pairs = {
    "China H-Shares (RMF)": {"ticker": "ASHR", "scb": "SCBCE-RMF", "kkp": "KKP CHINA-H-RMF"},
    "Vietnam (RMF)": {"ticker": "VNM", "scb": "SCBVIET-RMF", "kkp": "KKP VIETNAM-H-RMF"},
    "Health Care (RMF)": {"ticker": "XLV", "scb": "SCBGH-RMF", "kkp": "KKP GHC-RMF"},
    "Gold (RMF)": {"ticker": "GC=F", "scb": "SCBGOLD-RMF", "kkp": "KKP GOLD-H-RMF"},
    "SET 50 (Thai RMF)": {"ticker": "^SET50.BK", "scb": "SCBSET50-RMF", "kkp": "KKP SET50-RMF"}
}

# --- Header ---
st.title("⚖️ Fund Sniper: RMF Battle Matrix")
st.caption(f"ศูนย์วิเคราะห์กองทุน RMF (SCB vs KKP) | อัปเดตตลาดโลก: {datetime.now().strftime('%H:%M:%S')}")

# --- Combined Market Scanner ---
st.subheader("📊 ตารางสแกนจังหวะสะสม (RSI 9 กลุ่มยุทธศาสตร์)")
with st.spinner("กำลังเจาะข้อมูลตลาดโลก..."):
    all_funds = {**strategic_pairs, **extended_pairs}
    summary_data = []
    for name, info in all_funds.items():
        rsi, chg = get_live_rsi(info['ticker'])
        # AI Decision Logic
        if rsi and rsi < 35: action = "🔥 ช้อนหนัก (Strong Buy)"
        elif rsi and rsi < 45: action = "📈 ทยอยเก็บ"
        elif rsi and rsi > 65: action = "🛡️ พักเงิน (Wait)"
        else: action = "⚖️ DCA ปกติ"
        
        summary_data.append({
            "กลุ่มสินทรัพย์": name,
            "RSI (14)": rsi if rsi else "N/A",
            "Change (%)": f"{chg:+.2f}%",
            "AI Suggestion": action,
            "ค่ายที่แนะนำ": "เน้น KKP" if rsi and rsi < 45 else "เน้น SCB"
        })
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

st.divider()

# --- Detailed Analysis Zone ---
st.subheader("🎯 เจาะลึก 4 คู่ยุทธศาสตร์ และคำนวณงบ eDCA")
selected_pair = st.selectbox("เลือกคู่กองทุนที่ต้องการลงทุนรอบนี้", list(strategic_pairs.keys()))
budget = st.number_input("ยอดเงินลงทุนรอบนี้ (บาท)", value=10000, step=1000)

info = strategic_pairs[selected_pair]
rsi_val, _ = get_live_rsi(info['ticker'])

# AI Suggestion Logic for Weight
default_kkp = 100 if rsi_val and rsi_val < 35 else 80 if rsi_val and rsi_val < 45 else 50

col_cards, col_res = st.columns([2, 1])

with col_cards:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="fund-card scb-line">
            <p style='color:#6366f1; font-weight:bold; font-size:0.8rem;'>SCB RMF</p>
            <h4 style='margin:0;'>{info['scb']}</h4>
            <p style='color:#64748b; font-size:0.8rem;'>{info['desc']}</p>
        </div>""", unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""<div class="fund-card kkp-line">
            <p style='color:#f59e0b; font-weight:bold; font-size:0.8rem;'>KKP RMF</p>
            <h4 style='margin:0;'>{info['kkp']}</h4>
            <p style='color:#64748b; font-size:0.8rem;'>เน้นบริหารเชิงรุก / ซื้อผ่าน Dime!</p>
        </div>""", unsafe_allow_html=True)
    
    kkp_weight = st.slider(f"ปรับน้ำหนัก KKP (%)", 0, 100, int(default_kkp))
    scb_weight = 100 - kkp_weight

with col_res:
    st.metric("RSI ปัจจุบัน", f"{rsi_val}")
    st.write("---")
    st.metric(f"ยอดซื้อ SCB ({scb_weight}%)", f"฿{budget * (scb_weight/100):,.2f}")
    st.metric(f"ยอดซื้อ KKP ({kkp_weight}%)", f"฿{budget * (kkp_weight/100):,.2f}")

# Strategy Note based on RSI
if rsi_val:
    st.markdown("<div class='strategy-note'>", unsafe_allow_html=True)
    if rsi_val < 40:
        st.write(f"**AI วิเคราะห์:** จังหวะ RSI ต่ำ ({rsi_val}) พี่โบ้ควรเน้นไปที่ **{info['kkp']}** เพราะกองทุน Active จะทำ Performance ได้ดีกว่าในช่วงตลาดฟื้นตัวครับ")
    elif rsi_val > 60:
        st.write(f"**AI วิเคราะห์:** ตลาดเริ่มตึงตัว (RSI {rsi_val}) แนะนำแบ่งเงินเก็บไว้ใน Dime! Save รับดอกเบี้ย 3% รอจังหวะย่อตัวค่อยช้อนเพิ่มครับ")
    else:
        st.write(f"**AI วิเคราะห์:** สภาวะปกติ แนะนำใช้ **{info['scb']}** เพื่อประหยัดค่าธรรมเนียมในการทำ DCA ระยะยาวครับ")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption("Suchat Engineering Trading System • เน้นความมั่งคั่งและสิทธิภาษีของวิศวกรโบ้")
