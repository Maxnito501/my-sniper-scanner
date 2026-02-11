import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ==========================================
# 1. ตั้งค่าหน้าจอ
# ==========================================
st.set_page_config(
    page_title="Momentum Radar (หุ้นซิ่ง)",
    page_icon="🔥",
    layout="centered"
)

st.markdown("""
<style>
    .fire-box { padding: 15px; background-color: #ffe5e5; border-radius: 10px; color: #721c24; border-left: 5px solid #ff4b4b; }
    .ice-box { padding: 15px; background-color: #e5f5ff; border-radius: 10px; color: #004085; border-left: 5px solid #007bff; }
    div.stButton > button { width: 100%; font-weight: bold; border-radius: 8px; height: 3em; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฟังก์ชันคำนวณ RSI (สูตรคณิตศาสตร์)
# ==========================================
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ==========================================
# 3. ส่วนแสดงผล
# ==========================================
st.title("🔥 Momentum Radar")
st.caption("เครื่องมือจับสัญญาณ 'หุ้นซิ่ง' (วัดความแรง + วอลุ่มเข้า)")

col_input, col_btn = st.columns([3, 1])
with col_input:
    symbol = st.text_input("ชื่อหุ้นสายซิ่ง (เช่น DELTA, HANA, JTS)", "").upper()
with col_btn:
    st.write("")
    st.write("")
    btn_check = st.button("🚀 วัดความแรง")

if btn_check and symbol:
    with st.spinner(f"🔥 กำลังวัดอุณหภูมิหุ้น {symbol}..."):
        try:
            ticker_name = f"{symbol}.BK" if not symbol.endswith(".BK") else symbol
            stock = yf.Ticker(ticker_name)
            
            # ดึงกราฟย้อนหลัง 3 เดือน (เพื่อคำนวณ RSI)
            hist = stock.history(period="3mo")
            
            if len(hist) < 15:
                st.error("ข้อมูลไม่พอคำนวณครับ (หุ้นเพิ่งเข้าตลาด?)")
            else:
                # คำนวณ RSI
                hist['RSI'] = calculate_rsi(hist)
                current_rsi = hist['RSI'].iloc[-1]
                
                # คำนวณ Volume (เทียบวันนี้ กับ ค่าเฉลี่ย 5 วัน)
                current_vol = hist['Volume'].iloc[-1]
                avg_vol = hist['Volume'].iloc[-6:-1].mean()
                vol_spike = current_vol / avg_vol if avg_vol > 0 else 0
                
                price = hist['Close'].iloc[-1]
                change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100

                # --- แสดงผล ---
                st.divider()
                st.metric(f"ราคา {symbol}", f"{price:.2f}", f"{change:.2f}%")
                
                col1, col2 = st.columns(2)
                
                # 1. มาตรวัด RSI (ความร้อนแรง)
                with col1:
                    st.subheader("🌡️ ความร้อน (RSI)")
                    if current_rsi > 70:
                        st.error(f"🔥 {current_rsi:.2f} (Overbought)\nร้อนจัด! ระวังโดนเทขาย")
                    elif 50 <= current_rsi <= 70:
                        st.success(f"🚀 {current_rsi:.2f} (Strong)\nกำลังพุ่ง! สวยงาม")
                    elif 30 <= current_rsi < 50:
                        st.warning(f"🐢 {current_rsi:.2f} (Weak)\nแรงตก พักตัว")
                    else:
                        st.info(f"❄️ {current_rsi:.2f} (Oversold)\nถูกเกินไป (อาจเด้ง)")
                
                # 2. มาตรวัด Volume (น้ำมันเชื้อเพลิง)
                with col2:
                    st.subheader("⛽ วอลุ่ม (Volume)")
                    if vol_spike > 2.0:
                        st.success(f"💥 {vol_spike:.1f} เท่า\n(วอลุ่มระเบิด! คนรุมซื้อ)")
                    elif vol_spike > 1.0:
                        st.warning(f"✅ {vol_spike:.1f} เท่า\n(ปกติ)")
                    else:
                        st.error(f"❌ {vol_spike:.1f} เท่า\n(แห้งเหี่ยว ไม่มีคนเล่น)")

                st.divider()
                
                # --- สรุปสถานะ ---
                if current_rsi > 50 and vol_spike > 1.5:
                    st.markdown(f"""
                    <div class="fire-box">
                        <h3>🚀 SITUATION: เครื่องติดแล้ว!</h3>
                        <p>หุ้นกำลังมี Momentum ขาขึ้น + วอลุ่มเข้าสนับสนุน<br>
                        <b>Action:</b> สายซิ่งเกาะรถไปได้ (แต่ตั้ง Stop Loss ด้วยนะ)</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif current_rsi > 80:
                    st.markdown(f"""
                    <div class="fire-box" style="background-color:#ffe6e6; border-color:red;">
                        <h3>⚠️ SITUATION: ระวังดอย! (RSI Overbought)</h3>
                        <p>ราคาขึ้นแรงเกินไปแล้ว เสี่ยงโดนตบลงมา<br>
                        <b>Action:</b> อย่าเพิ่งไล่ราคา รอให้ย่อก่อน</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="ice-box">
                        <h3>❄️ SITUATION: เครื่องเย็น / พักตัว</h3>
                        <p>ยังไม่มีแรงส่ง หรือวอลุ่มยังไม่มา<br>
                        <b>Action:</b> เฝ้าดูไปก่อน อย่าเพิ่งเข้า</p>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

elif btn_check and not symbol:
    st.warning("ใส่ชื่อหุ้นก่อนซิ่งครับพี่!")
