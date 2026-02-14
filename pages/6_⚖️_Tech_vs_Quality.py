import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# --- การตั้งค่าหน้ากระดาษ ---
st.set_page_config(
    page_title="Fund Sniper: SCB vs KKP Decision",
    page_icon="⚖️",
    layout="wide"
)

# --- ปรับแต่ง UI ให้ดูพรีเมียมและสะอาดตา (Light Theme) ---
st.markdown("""
    <style>
    /* พื้นหลังสีอ่อนสว่าง */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* กล่อง Metric */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
    }

    /* การ์ดตัดสินใจรายคู่ */
    .decision-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 20px;
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        transition: transform 0.2s;
    }
    .decision-card:hover {
        transform: translateY(-2px);
    }

    /* แถบสีระบุค่ายกองทุน */
    .scb-highlight { border-left: 10px solid #6366f1; }
    .kkp-highlight { border-left: 10px solid #f59e0b; }

    /* หัวข้อภาษาไทย */
    h1, h2, h3, h4 {
        color: #0f172a !important;
        font-family: 'Kanit', sans-serif;
    }

    /* กล่องยุทธศาสตร์ */
    .strategy-note {
        background-color: #f1f5f9;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #334155;
        font-size: 0.95rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ฟังก์ชันคำนวณ RSI จากข้อมูลจริง ---
def get_live_rsi(ticker):
    try:
        # ดึงข้อมูลย้อนหลัง 1 เดือน
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if data.empty: return None, 0
        
        # ปรับรูปแบบข้อมูลให้เป็น Series ตัวเลขตัวเดียว
        if isinstance(data['Close'], pd.DataFrame):
            close = data['Close'].iloc[:, 0]
        else:
            close = data['Close']
            
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        
        # ดึงค่าล่าสุด
        rsi_val = float(rsi_series.iloc[-1])
        curr_p = float(close.iloc[-1])
        prev_p = float(close.iloc[-2])
        change = ((curr_p - prev_p) / prev_p) * 100
        
        if pd.isna(rsi_val): return None, 0
        return round(rsi_val, 2), round(change, 2)
    except:
        return None, 0

# --- ยุทธศาสตร์การตัดสินใจตามค่า RSI ---
def get_battle_decision(rsi):
    if rsi is None: return 50, "⚖️ รอข้อมูลตลาด"
    
    # เกณฑ์การตัดสินใจแบบ eDCA
    if rsi < 35:
        return 100, "🔥 ช้อนหนัก (KKP Focused)"
    elif rsi < 45:
        return 80, "📈 ทยอยเก็บ (KKP Advantage)"
    elif rsi > 65:
        return 0, "🛡️ หมอบก่อน (Overbought)"
    elif rsi > 55:
        return 20, "⚠️ ชะลอการซื้อ"
    else:
        return 50, "⚖️ DCA ปกติ (SCB Balanced)"

# --- ฐานข้อมูลกองทุน 4 คู่ยุทธศาสตร์ของพี่โบ้ ---
strategic_pairs = {
    "S&P 500 (ตลาดหุ้นสหรัฐฯ)": {
        "ticker": "^GSPC",
        "scb": "SCBRMS&P500",
        "kkp": "KKP S&P500 SET-RMF",
        "scb_note": "เน้นค่าธรรมเนียมต่ำที่สุดในไทย",
        "kkp_note": "ซื้อขายสะดวกผ่าน Dime! เริ่ม 1 บาท"
    },
    "Nasdaq 100 (หุ้นเทคโนโลยี)": {
        "ticker": "^NDX",
        "scb": "SCBNDQ",
        "kkp": "KKP NDQ100-H-RMF",
        "scb_note": "Unhedged (ลุ้นค่าเงินดอลลาร์)",
        "kkp_note": "Hedged (ป้องกันความเสี่ยงค่าเงิน)"
    },
    "Global Quality (หุ้นโลกคุณภาพ)": {
        "ticker": "QUAL",
        "scb": "SCBGQUAL",
        "kkp": "KKP GNP RMF-UH",
        "scb_note": "Passive Quality ดัชนีระดับโลก",
        "kkp_note": "Active (Capital Group) คัดหุ้นผู้ชนะ"
    },
    "Semiconductor (ชิป & AI)": {
        "ticker": "SOXX",
        "scb": "SCBSEMI",
        "kkp": "KKP TECH-H-RMF",
        "scb_note": "เน้นกลุ่มผู้ผลิต Chip โดยตรง",
        "kkp_note": "กระจายตัวในกลุ่ม AI Service & Software"
    }
}

# --- ส่วนหัวของแอป ---
st.title("🎯 Fund Sniper: SCB vs KKP Decision")
st.markdown("### ยุทธศาสตร์ช้อนกองทุน RMF 4 คู่หลัก")
st.caption(f"ข้อมูล Real-time RSI อัปเดตเมื่อ: {datetime.now().strftime('%H:%M:%S')}")

# --- ตารางสรุปภาพรวม (Summary Matrix) ---
with st.spinner("กำลังเจาะข้อมูลตลาดโลก..."):
    summary_list = []
    for name, info in strategic_pairs.items():
        rsi, chg = get_live_rsi(info['ticker'])
        weight, action = get_battle_decision(rsi)
        summary_list.append({
            "กลุ่มสินทรัพย์": name,
            "RSI (14 วัน)": rsi if rsi else "N/A",
            "Change (%)": f"{chg:+.2f}%",
            "จังหวะการลงทุน": action,
            "น้ำหนักแนะนำ (%)": f"{weight}%"
        })
    st.dataframe(pd.DataFrame(summary_list), use_container_width=True, hide_index=True)

st.divider()

# --- รายละเอียดการตัดสินใจรายคู่ ---
st.subheader("🔍 วิเคราะห์เจาะลึกรายคู่ (Decision Matrix)")

for name, info in strategic_pairs.items():
    rsi, chg = get_live_rsi(info['ticker'])
    weight, action = get_battle_decision(rsi)
    
    # เปิดกล่องวิเคราะห์อัตโนมัติถ้า RSI ต่ำ (จังหวะช้อน)
    with st.expander(f"📌 {name} | RSI: {rsi} | สถานะ: {action}", expanded=(rsi is not None and rsi < 40)):
        col_info, col_dec = st.columns([2, 1])
        
        with col_info:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""<div class="decision-card scb-highlight">
                    <p style='color:#6366f1; font-weight:bold; font-size:0.8rem;'>SCB OPTION</p>
                    <h4 style='margin:0;'>{info['scb']}</h4>
                    <p style='font-size:0.85rem; color:#64748b; margin-top:5px;'>{info['scb_note']}</p>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="decision-card kkp-highlight">
                    <p style='color:#f59e0b; font-weight:bold; font-size:0.8rem;'>KKP OPTION</p>
                    <h4 style='margin:0;'>{info['kkp']}</h4>
                    <p style='font-size:0.85rem; color:#64748b; margin-top:5px;'>{info['kkp_note']}</p>
                </div>""", unsafe_allow_html=True)
        
        with col_dec:
            st.metric("สัดส่วนลงเงินรอบนี้", f"{weight}%")
            if weight >= 80:
                st.success("🔥 โอกาสทอง! ช้อนของถูก")
            elif weight == 0:
                st.error("🛑 แพงเกินไป! ถือเงินสดรอ")
            else:
                st.info("📈 รักษาวินัย eDCA")

# --- เครื่องคิดเลขคำนวณยอดเงินลงทุน ---
st.divider()
st.subheader("🧮 เครื่องคิดเลขจัดสรรงบ eDCA")

c_sel, c_bud = st.columns([2, 1])
with c_sel:
    target_pair = st.selectbox("เลือกกองทุนที่จะลงทุนรอบนี้", list(strategic_pairs.keys()))
with c_bud:
    budget = st.number_input("ยอดงบประมาณ (บาท)", value=10000, step=1000)

rsi_calc, _ = get_live_rsi(strategic_pairs[target_pair]['ticker'])
sugg_weight, _ = get_battle_decision(rsi_calc)

# ปรับสัดส่วนตาม RSI (AI แนะนำเบื้องต้น)
final_kkp_weight = st.slider(f"สัดส่วน KKP สำหรับ {target_pair} (%)", 0, 100, int(sugg_weight))
final_scb_weight = 100 - final_kkp_weight

amt_scb = budget * (final_scb_weight / 100)
amt_kkp = budget * (final_kkp_weight / 100)

res1, res2, res3 = st.columns(3)
res1.metric(f"ยอดซื้อ SCB ({final_scb_weight}%)", f"฿{amt_scb:,.2f}")
res2.metric(f"ยอดซื้อ KKP ({final_kkp_weight}%)", f"฿{amt_kkp:,.2f}")
res3.metric("RSI ปัจจุบัน", f"{rsi_calc}")

# บทวิเคราะห์จาก AI
if rsi_calc:
    st.markdown("<div class='strategy-note'>", unsafe_allow_html=True)
    if rsi_calc < 35:
        st.write(f"**💡 คำแนะนำวิศวกร:** RSI {rsi_calc} อยู่ในโซนถูกมากครับพี่โบ้! แนะนำเทน้ำหนักไปที่ **{strategic_pairs[target_pair]['kkp']}** เพราะในจังหวะตลาดฟื้นตัว กองทุนที่เน้นความเร็วและการบริหารเชิงรุกจะให้ผลตอบแทนที่ดีกว่าครับ")
    elif rsi_calc > 65:
        st.write(f"**💡 คำแนะนำวิศวกร:** ตลาดร้อนแรงเกินไป (RSI {rsi_calc}) พี่โบ้เก็บเงินสดไว้ในบัญชี Dime! รับดอกเบี้ย 3% รอจังหวะย่อตัวดีกว่าครับ อย่าเพิ่งไปไล่ราคาตอนนี้")
    else:
        st.write(f"**💡 คำแนะนำวิศวกร:** สภาวะตลาดปกติ (RSI {rsi_calc}) แนะนำแบ่งเงินลงทุน SCB และ KKP สัดส่วนละครึ่งเพื่อให้ได้ทั้งความมั่นคงและโอกาสเติบโตครับ")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption("Suchat Engineering Trading System • พัฒนาเพื่อการตัดสินใจที่เฉียบคมของพี่โบ้")
