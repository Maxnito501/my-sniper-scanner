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

# --- Comprehensive Fund Database (RMF Selection) ---
fund_db = {
    "S&P 500 (ตลาดสหรัฐฯ)": {
        "ticker": "^GSPC",
        "scb": "SCBRMS&P500",
        "kkp": "KKP S&P500 SET-RMF",
        "desc": "หุ้นใหญ่สหรัฐฯ 500 ตัว (Core Portfolio)"
    },
    "Nasdaq 100 (หุ้นเทคโนโลยี)": {
        "ticker": "^NDX",
        "scb": "SCBNDQRMF",
        "kkp": "KKP NDQ100-H-RMF",
        "desc": "หุ้นนวัตกรรมและเทคฯ ระดับโลก"
    },
    "Global Quality (หุ้นโลกผู้ชนะ)": {
        "ticker": "QUAL",
        "scb": "SCBGQUAL-RMF",
        "kkp": "KKP GNP RMF-UH",
        "desc": "คัดหุ้นคุณภาพพื้นฐานแกร่งทั่วโลก"
    },
    "Semiconductor (ชิป & AI)": {
        "ticker": "SOXX",
        "scb": "SCBSEMI-RMF",
        "kkp": "KKP TECH-H-RMF",
        "desc": "กลุ่มชิปประมวลผลและ Software AI"
    },
    "China H-Shares (หุ้นจีน)": {
        "ticker": "ASHR",
        "scb": "SCBCE-RMF",
        "kkp": "KKP CHINA-H-RMF",
        "desc": "หุ้นจีนแผ่นดินใหญ่ (Value Play)"
    },
    "Vietnam (หุ้นเวียดนาม)": {
        "ticker": "VNM",
        "scb": "SCBVIET-RMF",
        "kkp": "KKP VIETNAM-H-RMF",
        "desc": "หุ้นเวียดนาม ตลาดเกิดใหม่ศักยภาพสูง"
    },
    "Health Care (หุ้นสุขภาพ)": {
        "ticker": "XLV",
        "scb": "SCBGH-RMF",
        "kkp": "KKP GHC-RMF",
        "desc": "กลุ่มการแพทย์และสุขภาพ (Defensive)"
    },
    "Gold (ทองคำ)": {
        "ticker": "GC=F",
        "scb": "SCBGOLD-RMF",
        "kkp": "KKP GOLD-H-RMF",
        "desc": "สินทรัพย์ปลอดภัย ป้องกันความเสี่ยง"
    },
    "SET 50 (หุ้นไทย)": {
        "ticker": "^SET50.BK",
        "scb": "SCBSET50-RMF",
        "kkp": "KKP SET50-RMF",
        "desc": "หุ้นใหญ่ 50 ตัวของประเทศไทย"
    }
}

# --- Header ---
st.title("⚖️ Fund Sniper: RMF Battle Matrix")
st.caption(f"ระบบเปรียบเทียบกองทุน RMF (SCB vs KKP) ครบทุกกลุ่ม | อัปเดตตลาดโลก: {datetime.now().strftime('%H:%M:%S')}")

# --- Global Market Scanner Table ---
st.subheader("📊 ตารางสแกนจังหวะเข้าช้อน (RSI 9 กลุ่ม)")
with st.spinner("กำลังเจาะข้อมูลตลาดโลก..."):
    summary_data = []
    for name, info in fund_db.items():
        rsi, chg = get_live_rsi(info['ticker'])
        # AI Logic for Suggestion
        if rsi and rsi < 35: action = "🔥 ช้อนหนัก (Strong Buy)"
        elif rsi and rsi < 45: action = "📈 ทยอยเก็บ"
        elif rsi and rsi > 65: action = "🛡️ พักเงิน (Wait)"
        else: action = "⚖️ DCA ปกติ"
        
        summary_data.append({
            "กลุ่มสินทรัพย์": name,
            "RSI (14)": rsi if rsi else "N/A",
            "Change (%)": f"{chg:+.2f}%",
            "คำแนะนำ AI": action,
            "ค่ายที่โดดเด่น": "เน้น KKP" if rsi and rsi < 45 else "เน้น SCB"
        })
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

st.divider()

# --- Detailed Analysis Zone ---
st.subheader("🎯 เจาะลึกรายตัวและจัดสรรงบ eDCA")
col_sel, col_bud = st.columns([2, 1])

with col_sel:
    selected_pair = st.selectbox("เลือกกองทุนที่จะลงเงินรอบนี้", list(fund_db.keys()))
with col_bud:
    budget = st.number_input("งบประมาณ (บาท)", value=10000, step=1000)

info = fund_db[selected_pair]
rsi_val, _ = get_live_rsi(info['ticker'])

# AI Weight Suggestion
default_kkp = 100 if rsi_val and rsi_val < 35 else 80 if rsi_val and rsi_val < 45 else 50 if rsi_val and rsi_val < 60 else 0

col_cards, col_res = st.columns([2, 1])

with col_cards:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="fund-card scb-line">
            <p style='color:#6366f1; font-weight:bold; font-size:0.8rem;'>SCB RMF (InnovestX)</p>
            <h4 style='margin:0;'>{info['scb']}</h4>
            <p style='color:#64748b; font-size:0.8rem;'>{info['desc']}</p>
        </div>""", unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""<div class="fund-card kkp-line">
            <p style='color:#f59e0b; font-weight:bold; font-size:0.8rem;'>KKP RMF (Dime!)</p>
            <h4 style='margin:0;'>{info['kkp']}</h4>
            <p style='color:#64748b; font-size:0.8rem;'>เน้นบริหารเชิงรุก / ป้องกันค่าเงิน</p>
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
        st.write(f"**💡 AI Sniper Analysis:** จังหวะ RSI ต่ำ ({rsi_val}) พี่โบ้ควรเน้นช้อนไปที่ **{info['kkp']}** ในแอป Dime! ครับ เพราะกองทุนที่บริหารแบบ Active จะทำผลงานได้ดีกว่ามากในช่วงที่ตลาดเริ่มฟื้นตัวจากจุดต่ำสุด")
    elif rsi_val > 65:
        st.write(f"**💡 AI Sniper Analysis:** ตลาดเข้าเขต Overbought (RSI {rsi_val}) แล้วครับ พี่โบ้ควรพักการซื้อกองทุนนี้ไว้ก่อน หรือโยนเงินไปพักในบัญชี Dime! Save รับดอกเบี้ย 3% รอจังหวะย่อตัวรอบหน้าครับ")
    else:
        st.write(f"**💡 AI Sniper Analysis:** ตลาดอยู่ในโซนปกติ แนะนำใช้ **{info['scb']}** เพื่อประหยัดค่าใช้จ่ายการจัดการ (Fee) ในการทำ DCA ระยะยาวครับ")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption("Suchat Engineering Trading System • คัดกรองกองทุนเพื่อความมั่งคั่งของพี่โบ้")
