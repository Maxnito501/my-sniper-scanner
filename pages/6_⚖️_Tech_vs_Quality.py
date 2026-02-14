import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# --- Configuration ---
st.set_page_config(
    page_title="Fund Sniper: Reversal Detector",
    page_icon="🎯",
    layout="wide"
)

# --- Custom Styling (Premium Light Theme) ---
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
    .reversal-glow {
        background: linear-gradient(90deg, #ffffff 0%, #f0fdf4 100%);
        border: 1px solid #22c55e;
    }
    .strategy-note {
        background-color: #f1f5f9;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #334155;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Enhanced Analysis Logic ---
def get_detailed_analysis(ticker):
    try:
        data = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if data.empty: return None
        
        # จัดการข้อมูลกรณี MultiIndex
        if isinstance(data['Close'], pd.DataFrame):
            close = data['Close'].iloc[:, 0]
        else:
            close = data['Close']
        
        # 1. RSI Calculation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 2. Moving Average (Trend)
        ma20 = close.rolling(window=20).mean()
        
        # 3. Reversal Signal Logic
        recent_low = close.iloc[-5:].min()
        curr_price = close.iloc[-1]
        last_rsi = float(rsi.iloc[-1])
        is_reversing = (last_rsi < 45) and (curr_price > recent_low)
        
        # 4. Momentum
        roc = ((curr_price - close.iloc[-5]) / close.iloc[-5]) * 100
        change = ((curr_price - close.iloc[-2]) / close.iloc[-2]) * 100
        
        return {
            "price": round(float(curr_price), 2),
            "change": round(float(change), 2),
            "rsi": round(last_rsi, 2),
            "ma20": round(float(ma20.iloc[-1]), 2),
            "is_reversing": is_reversing,
            "roc": round(float(roc), 2),
            "trend": "BULL" if curr_price > ma20.iloc[-1] else "BEAR"
        }
    except:
        return None

# --- Fund Database ---
fund_db = {
    "Nasdaq 100 (Tech)": {"ticker": "^NDX", "scb": "SCBNDQRMF", "kkp": "KKP NDQ100-H-RMF"},
    "S&P 500 (US)": {"ticker": "^GSPC", "scb": "SCBRMS&P500", "kkp": "KKP S&P500 SET-RMF"},
    "Global Quality": {"ticker": "QUAL", "scb": "SCBGQUAL-RMF", "kkp": "KKP GNP RMF-UH"},
    "Semiconductor": {"ticker": "SOXX", "scb": "SCBSEMI-RMF", "kkp": "KKP TECH-H-RMF"}
}

# --- Header ---
st.title("🎯 Fund Sniper: Reversal Detector")
st.caption(f"ระบบตรวจจับจุดกลับตัวเพื่อช้อนกองทุน RMF | {datetime.now().strftime('%H:%M:%S')}")

# --- Sniper Dashboard ---
st.subheader("🚀 Reversal Scanner (ตรวจจับสัญญาณกลับตัว)")
cols = st.columns(len(fund_db))

for i, (name, info) in enumerate(fund_db.items()):
    analysis = get_detailed_analysis(info['ticker'])
    with cols[i]:
        if analysis:
            st.metric(name, f"{analysis['price']}", f"{analysis['change']}%")
            if analysis['is_reversing']:
                st.success("✅ สัญญาณกลับตัว!")
            else:
                st.info("⏳ รอจังหวะ...")
            st.write(f"RSI: {analysis['rsi']}")
        else:
            st.error("Data Error")

st.divider()

# --- Tactical Selection ---
st.subheader("🧮 แผนภูมิคำนวณการช้อน (Decision Matrix)")
selected_name = st.selectbox("เลือกกองทุนที่จะวิเคราะห์จุดกลับหัว", list(fund_db.keys()))
budget = st.number_input("งบประมาณ (บาท)", value=10000, step=1000)

analysis = get_detailed_analysis(fund_db[selected_name]['ticker'])
info = fund_db[selected_name]

if analysis:
    col_card, col_calc = st.columns([2, 1])
    
    with col_card:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="fund-card scb-line">
                <p style='color:#6366f1; font-weight:bold; font-size:0.8rem;'>SCB RMF</p>
                <h4 style='margin:0;'>{info['scb']}</h4>
                <p style='color:#64748b; font-size:0.8rem;'>เน้นความมั่นคง / ค่าธรรมเนียมต่ำ</p>
            </div>""", unsafe_allow_html=True)
        with c2:
            glow_class = "reversal-glow" if analysis['is_reversing'] else ""
            st.markdown(f"""<div class="fund-card kkp-line {glow_class}">
                <p style='color:#f59e0b; font-weight:bold; font-size:0.8rem;'>KKP RMF (Sniper Choice)</p>
                <h4 style='margin:0;'>{info['kkp']}</h4>
                <p style='color:#64748b; font-size:0.8rem;'>เน้น Active / ช้อนใน Dime!</p>
            </div>""", unsafe_allow_html=True)

        # Slider สัดส่วน
        sugg_kkp = 100 if analysis['is_reversing'] else 80 if analysis['rsi'] < 40 else 50
        kkp_w = st.slider("สัดส่วน KKP (%)", 0, 100, int(sugg_kkp))
        scb_w = 100 - kkp_w
        
    with col_calc:
        r1, r2, r3 = st.columns(3)
        # แสดงผลลัพธ์ในกรอบเดียวกับเครื่องคิดเลข
        st.metric("ยอดช้อน SCB", f"฿{budget*(scb_w/100):,.2f}")
        st.metric("ยอดช้อน KKP", f"฿{budget*(kkp_w/100):,.2f}")
        st.metric("Reversal Prob.", "HIGH" if analysis['is_reversing'] else "LOW")

    # AI Commentary
    st.markdown("<div class='strategy-note'>", unsafe_allow_html=True)
    if analysis['is_reversing']:
        st.write(f"**💡 Sniper Analysis:** พี่โบ้ครับ! กราฟ {selected_name} เริ่มมีอาการ **'งัดหัวขึ้น'** หลังจากลงไปลึก (RSI {analysis['rsi']}) ราคามักจะดีดไวมาก แนะนำให้กดซื้อ **{info['kkp']}** เช้าวันจันทร์นี้ให้ทันครับ")
    elif analysis['rsi'] < 30:
        st.write(f"**💡 Sniper Analysis:** RSI {analysis['rsi']} ต่ำมากแต่ราคายังไม่นิ่ง ระวังการกลับหัวกะทันหัน แบ่งไม้ซื้อ 50% กันตกรถก่อนได้ครับ")
    else:
        st.write(f"**💡 Sniper Analysis:** ราคายังแกว่งตัวในแนวโน้ม {analysis['trend']} รอให้ RSI ลงต่ำกว่า 40 หรือมีสัญญาณงัดหัวชัดๆ ค่อยอัดเต็มข้อครับ")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption("Suchat Strategy Center • ระบบตรวจจับจุดกลับหัวอัตโนมัติ")
