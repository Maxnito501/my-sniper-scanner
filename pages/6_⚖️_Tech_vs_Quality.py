import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Tech vs Quality Balancer", page_icon="⚖️", layout="wide")

st.title("⚖️ Tech vs Quality Balancer: จัดทัพ EDCA")
st.markdown("""
**เครื่องมือชั่งน้ำหนักการลงทุน: เปรียบเทียบความน่าสนใจระหว่าง 'หุ้นชิป (Growth)' และ 'หุ้นแกร่ง (Quality)'**
* 🤖 **AI Suggestion:** แนะนำสัดส่วนการลงทุน (Weight) ตามค่า RSI ปัจจุบัน
* 📉 **RSI Compare:** ดูกราฟเทียบกันชัดๆ ว่าตัวไหนถูกกว่า
""")
st.write("---")

# --- 2. Sidebar Input ---
st.sidebar.header("💰 เงินกระสุน (Budget)")
budget = st.sidebar.number_input("เงินที่จะลงทุนรอบนี้ (บาท)", value=4000, step=500)
st.sidebar.caption("ระบบจะคำนวณแบ่งเงินให้ตามความน่าสนใจ")

# --- 3. ฟังก์ชันคำนวณ ---
@st.cache_data(ttl=60) # Cache 1 นาที
def get_pair_data():
    try:
        # ดึงข้อมูล 2 ตัวพร้อมกัน (SMH = Semi, QUAL = Quality)
        df = yf.download("SMH QUAL", period="6mo", interval="1d", progress=False)
        
        # แก้ปัญหา MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            close_df = df['Close']
        else:
            close_df = df['Close'] # Fallback
            
        return close_df
    except: return None

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- 4. Main Logic ---
df = get_pair_data()

if df is not None:
    # คำนวณ RSI ล่าสุด
    rsi_semi = calculate_rsi(df['SMH']).iloc[-1]
    rsi_qual = calculate_rsi(df['QUAL']).iloc[-1]
    
    price_semi = df['SMH'].iloc[-1]
    price_qual = df['QUAL'].iloc[-1]

    # --- 5. Algorithm ถ่วงน้ำหนัก (The Brain) ---
    weight_semi = 0
    weight_qual = 0
    advice = ""
    color_box = "#f3f4f6"
    text_color = "black"

    # Case 1: แพงทั้งคู่ (RSI > 60) -> ไม่ซื้อ
    if rsi_semi > 60 and rsi_qual > 60:
        advice = "⛔ WAIT: แพงทั้งคู่! กำเงินสดรอ (Overbought)"
        weight_semi = 0
        weight_qual = 0
        color_box = "#fee2e2" # แดงอ่อน
        
    # Case 2: ถูกทั้งคู่ (RSI < 40) -> จัดเต็ม
    elif rsi_semi < 40 and rsi_qual < 40:
        advice = "💎 DOUBLE DIP: ถูกทั้งคู่! แบ่งครึ่งหรือเน้นตัวที่ชอบ"
        weight_semi = 50
        weight_qual = 50
        color_box = "#dcfce7" # เขียวอ่อน
        
    # Case 3: Semi ถูกกว่า (น่าสนกว่า)
    elif rsi_semi < rsi_qual:
        # ยิ่ง RSI Semi ต่ำ ยิ่งน่าเพิ่มน้ำหนัก
        diff = rsi_qual - rsi_semi
        if diff > 10: # ต่างกันเยอะ
            weight_semi = 70
            weight_qual = 30
            advice = f"🚀 FOCUS SEMI: ชิปถูกกว่ามาก (Gap {diff:.1f}) -> เน้น Semi"
        else: # ต่างกันนิดหน่อย
            weight_semi = 60
            weight_qual = 40
            advice = f"⚖️ TILT SEMI: ชิปถูกกว่านิดหน่อย -> เพิ่มน้ำหนัก Semi"
        color_box = "#e0f2fe" # ฟ้าอ่อน

    # Case 4: Quality ถูกกว่า
    else: # rsi_qual < rsi_semi
        diff = rsi_semi - rsi_qual
        if diff > 10:
            weight_semi = 30
            weight_qual = 70
            advice = f"🛡️ FOCUS QUALITY: หุ้นแกร่งถูกกว่า (Gap {diff:.1f}) -> เน้น Quality"
        else:
            weight_semi = 40
            weight_qual = 60
            advice = f"⚖️ TILT QUALITY: หุ้นแกร่งถูกกว่านิดหน่อย -> เพิ่มน้ำหนัก Quality"
        color_box = "#fff7ed" # ส้มอ่อน

    # คำนวณเงิน
    money_semi = budget * (weight_semi / 100)
    money_qual = budget * (weight_qual / 100)

    # --- 6. แสดงผล Dashboard ---
    
    # กล่องสรุป
    st.markdown(f"""
    <div style="background-color: {color_box}; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #ccc;">
        <h2 style="margin:0; color: {text_color};">🤖 {advice}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")

    # การ์ดเปรียบเทียบ
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🚀 SCBSEMI (Semi-Conductor)")
        st.caption("ตัวแทน: SMH (VanEck Semiconductor)")
        st.metric("RSI (Momentum)", f"{rsi_semi:.1f}", delta=f"{rsi_semi-50:.1f} จากค่ากลาง", delta_color="inverse")
        st.metric("แนะนำลงทุน", f"{money_semi:,.0f} บาท", f"สัดส่วน {weight_semi}%")
        if weight_semi > 50: st.success("✅ ตัวเลือกหลักรอบนี้")
        
    with c2:
        st.subheader("🛡️ SCBGQUAL (Global Quality)")
        st.caption("ตัวแทน: QUAL (iShares MSCI USA Quality)")
        st.metric("RSI (Momentum)", f"{rsi_qual:.1f}", delta=f"{rsi_qual-50:.1f} จากค่ากลาง", delta_color="inverse")
        st.metric("แนะนำลงทุน", f"{money_qual:,.0f} บาท", f"สัดส่วน {weight_qual}%")
        if weight_qual > 50: st.success("✅ ตัวเลือกหลักรอบนี้")

    st.write("---")

    # กราฟ RSI เปรียบเทียบ
    st.subheader("📉 กราฟ RSI: ใครถูกกว่ากัน?")
    
    # สร้างข้อมูล RSI ย้อนหลัง
    rsi_semi_series = calculate_rsi(df['SMH'])
    rsi_qual_series = calculate_rsi(df['QUAL'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=rsi_semi_series, name='SCBSEMI (SMH)', line=dict(color='red', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=rsi_qual_series, name='SCBGQUAL (QUAL)', line=dict(color='blue', width=2)))
    
    # เส้นโซน
    fig.add_hline(y=70, line_dash="dot", line_color="gray", annotation_text="Overbought (แพง)")
    fig.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="Oversold (ถูก)")
    fig.add_hrect(y0=30, y1=70, line_width=0, fillcolor="gray", opacity=0.1)
    
    fig.update_layout(height=400, hovermode="x unified", yaxis_title="RSI Value")
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("💡 **วิธีดู:** เส้นไหนอยู่ต่ำกว่า = ถูกกว่า (น่าสนใจกว่า) | ถ้าอยู่ต่ำทั้งคู่ = น่าสนใจที่สุด")

else:
    st.error("ไม่สามารถดึงข้อมูลเปรียบเทียบได้")