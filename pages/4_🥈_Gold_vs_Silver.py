import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import datetime

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Gold vs Silver Analyzer", page_icon="🥈", layout="wide")

st.title("🥈 Silver vs 🥇 Gold: The Engineer's Comparison")
st.markdown("**วิเคราะห์ความสัมพันธ์และหาจังหวะเข้าซื้อด้วย 'Gold/Silver Ratio'**")
st.write("---")

# --- Sidebar ---
st.sidebar.header("⚙️ ตั้งค่าช่วงเวลา")
period = st.sidebar.select_slider("ระยะเวลาย้อนหลัง", options=["1mo", "3mo", "6mo", "1y", "5y", "10y"], value="1y")

# --- 1. ดึงข้อมูล ---
@st.cache_data(ttl=3600)
def get_metal_data(period):
    try:
        # GLD = กองทุนทองคำโลก, SLV = กองทุนเงินโลก
        data = yf.download("GLD SLV", period=period, interval="1d", progress=False)['Close']
        return data
    except: return None

df = get_metal_data(period)

if df is not None:
    # --- 2. คำนวณ Gold/Silver Ratio ---
    # (ราคา Gold ต่อออนซ์ / ราคา Silver ต่อออนซ์)
    # หมายเหตุ: GLD/SLV เป็นราคา ETF ต้องคูณสัดส่วนกลับ แต่ดูเทรนด์คร่าวๆ จากราคา ETF ได้เลย
    ratio = df['GLD'] / df['SLV']
    current_ratio = ratio.iloc[-1]
    
    # --- 3. ส่วนแสดงผล (Dashboard) ---
    col1, col2, col3 = st.columns(3)
    
    # Performance Comparison (Normalize to %)
    df_norm = (df / df.iloc[0]) * 100
    gld_perf = df_norm['GLD'].iloc[-1] - 100
    slv_perf = df_norm['SLV'].iloc[-1] - 100
    
    with col1:
        st.metric("🥇 Gold Performance", f"{gld_perf:+.2f}%", help="เทียบกับจุดเริ่มต้นของช่วงเวลา")
    with col2:
        st.metric("🥈 Silver Performance", f"{slv_perf:+.2f}%", help="Silver มักจะเหวี่ยงแรงกว่า")
        
    with col3:
        # Logic การอ่านค่า Ratio (สูตรวิศวะ)
        # Ratio สูง (>80) = ทองแพง/เงินถูก -> น่าซื้อเงิน
        # Ratio ต่ำ (<50) = ทองถูก/เงินแพง -> น่าซื้อทอง
        advice = ""
        color = "off"
        if current_ratio > 80:
            advice = "🟢 Silver ถูกมาก! (น่าสะสม)"
            color = "normal"
        elif current_ratio < 60:
            advice = "🔴 Silver แพงแล้ว (ระวัง)"
            color = "inverse"
        else:
            advice = "⚪ ราคาสมดุล (Fair)"
            color = "off"
            
        st.metric("⚖️ Gold/Silver Ratio", f"{current_ratio:.2f}", advice)

    # --- 4. กราฟเปรียบเทียบ (Normalized) ---
    st.subheader("📈 กราฟวัดความแรง (ใครวิ่งเร็วกว่ากัน?)")
    st.caption("กราฟเริ่มที่ 100% เท่ากัน เพื่อดูว่าใครเติบโตได้ดีกว่า")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_norm.index, y=df_norm['GLD'], name='Gold (GLD)', line=dict(color='gold', width=2)))
    fig.add_trace(go.Scatter(x=df_norm.index, y=df_norm['SLV'], name='Silver (SLV)', line=dict(color='silver', width=2)))
    fig.update_layout(height=450, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # --- 5. กราฟ Ratio (จับจังหวะสับเปลี่ยน) ---
    st.subheader("🎚️ กราฟ Gold/Silver Ratio (ดัชนีความถูกแพง)")
    st.caption("ถ้ายอดกราฟ **สูง** แปลว่า **Silver ถูก** (น่าซื้อ) | ถ้ายอดกราฟ **ต่ำ** แปลว่า **Silver แพง**")
    
    fig_ratio = go.Figure()
    fig_ratio.add_trace(go.Scatter(x=ratio.index, y=ratio, name='Ratio', line=dict(color='#3b82f6'), fill='tozeroy'))
    
    # เส้นเกณฑ์มาตรฐาน
    fig_ratio.add_hline(y=80, line_dash="dot", line_color="green", annotation_text="โซนน่าซื้อ Silver")
    fig_ratio.add_hline(y=60, line_dash="dot", line_color="red", annotation_text="โซนน่าขาย Silver")
    
    fig_ratio.update_layout(height=300)
    st.plotly_chart(fig_ratio, use_container_width=True)
    
    # --- 6. บทวิเคราะห์วิศวกร ---
    st.info("""
    ### 👨‍🔧 Engineering Insight:
    1.  **Correlation:** สังเกตไหมครับ? เส้นสีทองกับสีเงินจะวิ่ง **"ทิศทางเดียวกัน"** เกือบตลอดเวลา
    2.  **Amplitude (ความกว้างคลื่น):** เส้นสีเงิน (Silver) จะมีความชันและความลึกมากกว่า (High Beta) 
        * *ตอนขึ้น:* เงินจะวิ่งแซงทอง
        * *ตอนลง:* เงินจะลงหนักกว่าทอง
    3.  **กลยุทธ์ Sniper:** * ถ้าเชื่อว่าเศรษฐกิจโลกจะฟื้นตัว หรืออุตสาหกรรม EV/Solar มาแรง -> **Silver ชนะขาด**
        * ถ้ากลัวสงคราม/เศรษฐกิจพัง -> **Gold ปลอดภัยกว่า**
    """)

else:
    st.error("ไม่สามารถดึงข้อมูลได้")
