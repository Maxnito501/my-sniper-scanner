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
# 2. ฐานข้อมูลหุ้นซิ่ง (The Watchlist)
# ==========================================
# รวมรายชื่อหุ้นที่ขึ้นชื่อเรื่องความผันผวนและวอลุ่ม
speculative_stocks = {
    "พิมพ์เอง (Custom)": [],
    "🔥 แก๊งค์อิเล็กฯ (ตัวแรง)": ["DELTA", "HANA", "KCE", "CCET", "SVI"],
    "💻 แก๊งค์ Tech & Crypto": ["JTS", "ZIGA", "XPG", "BROOK", "MVP"],
    "⚡ แก๊งค์ EV & Energy": ["EA", "NEX", "BYD", "PSP"],
    "💃 แก๊งค์กระแส (นางงาม/บันเทิง)": ["MGI", "MONO", "ONEE", "WORK"],
    "🏗️ แก๊งค์รับเหมา & ก่อสร้าง": ["ITD", "NWR", "TRC", "CNT"],
    "🎲 แก๊งค์หุ้นเล็ก (Small Cap)": ["PROEN", "PSG", "SABUY", "NUSA", "SKE"],
    "🏦 แก๊งค์การเงิน (Consumer Finance)": ["TIDLOR", "MTC", "SAWAD", "CHAYO"]
}

# ==========================================
# 3. ฟังก์ชันคำนวณ RSI
# ==========================================
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ==========================================
# 4. ส่วนแสดงผล (UI)
# ==========================================
st.title("🔥 Momentum Radar")
st.caption("เครื่องมือจับสัญญาณ 'หุ้นซิ่ง' (วัดความแรง RSI + วอลุ่มระเบิด)")

# --- ส่วนเลือกหุ้น (Dropdown Menu) ---
with st.container():
    st.subheader("🎯 เลือกเป้าหมาย")
    col_cat, col_stock = st.columns(2)
    
    with col_cat:
        category = st.selectbox("หมวดหมู่หุ้นซิ่ง", list(speculative_stocks.keys()))
    
    with col_stock:
        # ถ้าเลือกพิมพ์เอง ให้ขึ้นช่องว่าง
        if category == "พิมพ์เอง (Custom)":
            selected_stock = st.text_input("ระบุชื่อหุ้นเอง", "").upper()
        else:
            # ถ้าเลือกหมวด ให้ขึ้น List หุ้นในหมวดนั้น
            selected_stock = st.selectbox("เลือกหุ้นในแก๊งค์", speculative_stocks[category])

    btn_check = st.button("🚀 วัดความแรงทันที")

# ==========================================
# 5. ส่วนประมวลผล (Engine)
# ==========================================
if btn_check and selected_stock:
    # จัดการชื่อหุ้น (เผื่อ user พิมพ์ .BK มาเอง หรือไม่พิมพ์)
    symbol = selected_stock.replace(".BK", "").upper()
    
    with st.spinner(f"🔥 กำลังวัดอุณหภูมิ {symbol}..."):
        try:
            ticker_name = f"{symbol}.BK"
            stock = yf.Ticker(ticker_name)
            
            # ดึงข้อมูล 3 เดือน
            hist = stock.history(period="3mo")
            
            if len(hist) < 15:
                st.error(f"❌ ไม่พบข้อมูลหุ้น {symbol} หรือเพิ่งเข้าตลาด")
            else:
                # คำนวณ RSI
                hist['RSI'] = calculate_rsi(hist)
                current_rsi = hist['RSI'].iloc[-1]
                
                # คำนวณ Volume (เทียบวันนี้ กับ ค่าเฉลี่ย 5 วัน)
                current_vol = hist['Volume'].iloc[-1]
                avg_vol = hist['Volume'].iloc[-6:-1].mean()
                
                # ป้องกัน Error หารด้วยศูนย์
                if avg_vol == 0: avg_vol = 1 
                vol_spike = current_vol / avg_vol
                
                # ข้อมูลราคา
                price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = ((price - prev_price) / prev_price) * 100

                # --- แสดงผล ---
                st.divider()
                
                # แสดงหัวข้อใหญ่ๆ
                st.markdown(f"### 📊 ผลลัพธ์: {symbol}")
                
                # สีของราคา
                color_price = "green" if change >= 0 else "red"
                st.markdown(f"""
                <h2 style='color:{color_price}'>
                    {price:.2f} บาท ({change:+.2f}%)
                </h2>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                # 1. มาตรวัด RSI
                with col1:
                    st.write("🌡️ **ความร้อน (RSI)**")
                    if current_rsi > 75:
                        st.error(f"🔥 {current_rsi:.2f}\n(Overbought - ร้อนจัด!)")
                    elif 55 <= current_rsi <= 75:
                        st.success(f"🚀 {current_rsi:.2f}\n(Bullish - กำลังพุ่ง)")
                    elif 40 <= current_rsi < 55:
                        st.warning(f"🐢 {current_rsi:.2f}\n(Sideway - พักตัว)")
                    else:
                        st.info(f"❄️ {current_rsi:.2f}\n(Oversold - ลงลึก)")
                
                # 2. มาตรวัด Volume
                with col2:
                    st.write("⛽ **วอลุ่ม (Volume)**")
                    if vol_spike > 2.0:
                        st.success(f"💥 {vol_spike:.1f} เท่า\n(วอลุ่มระเบิด!)")
                    elif vol_spike > 1.0:
                        st.warning(f"✅ {vol_spike:.1f} เท่า\n(ปกติ)")
                    else:
                        st.error(f"❌ {vol_spike:.1f} เท่า\n(ตลาดวาย)")

                st.divider()
                
                # --- สรุปคำแนะนำ ---
                if current_rsi > 50 and vol_spike > 1.5 and change > 0:
                    st.markdown(f"""
                    <div class="fire-box">
                        <h3>🚀 SITUATION: เครื่องติดแล้ว! (Action Zone)</h3>
                        <p><b>สัญญาณ:</b> ราคาพุ่ง + มีวอลุ่มเจ้ามือดัน + RSI สวย<br>
                        <b>แผนการเล่น:</b> ตามน้ำได้ (Follow Buy) แต่ต้องตั้ง Stop Loss เสมอ!</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif current_rsi > 80:
                    st.markdown(f"""
                    <div class="fire-box" style="background-color:#ffe6e6; border-color:red;">
                        <h3>⚠️ SITUATION: ระวังดอย! (High Risk)</h3>
                        <p><b>สัญญาณ:</b> ร้อนแรงเกินไป (Overbought)<br>
                        <b>แผนการเล่น:</b> อย่าไล่ราคา! รอให้ย่อลงมาก่อนค่อยรับ</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif change < -2 and vol_spike > 1.5:
                     st.markdown(f"""
                    <div class="fire-box" style="background-color:#ffe6e6; border-color:red;">
                        <h3>🩸 SITUATION: ทิ้งของ! (Panic Sell)</h3>
                        <p><b>สัญญาณ:</b> ราคาลงหนัก + วอลุ่มขายถล่มทลาย<br>
                        <b>แผนการเล่น:</b> ห้ามรับมีด! รอให้ฝุ่นจางก่อน</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                else:
                    st.markdown(f"""
                    <div class="ice-box">
                        <h3>❄️ SITUATION: ยังไม่ซิ่ง (Wait & See)</h3>
                        <p><b>สัญญาณ:</b> วอลุ่มยังไม่เข้า หรือราคายังไม่ออกตัว<br>
                        <b>แผนการเล่น:</b> ใส่ Watchlist ไว้ก่อน อย่าเพิ่งเข้า</p>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

elif btn_check and not selected_stock:
    st.warning("⚠️ กรุณาเลือกหุ้นหรือพิมพ์ชื่อหุ้นก่อนครับ")
