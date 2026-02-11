import streamlit as st
import yfinance as yf

# ==========================================
# 1. ตั้งค่าหน้าจอ
# ==========================================
st.set_page_config(
    page_title="Buffett Value Scanner",
    page_icon="💎",
    layout="centered"
)

# CSS แต่งสวย
st.markdown("""
<style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .success-box { padding: 15px; background-color: #d4edda; border-radius: 10px; color: #155724; border-left: 5px solid #28a745; }
    .warning-box { padding: 15px; background-color: #fff3cd; border-radius: 10px; color: #856404; border-left: 5px solid #ffc107; }
    .error-box { padding: 15px; background-color: #f8d7da; border-radius: 10px; color: #721c24; border-left: 5px solid #dc3545; }
    div.stButton > button { width: 100%; font-weight: bold; border-radius: 8px; height: 3em; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฐานข้อมูลหุ้นคุณค่า (The Value List)
# ==========================================
value_stocks = {
    "พิมพ์เอง (Custom)": [],
    "🏦 แก๊งค์ปันผลเทพ (Banks & Finance)": ["TISCO", "KKP", "SCB", "BBL", "TCAP"],
    "🏠 แก๊งค์อสังหาฯ ปันผลดุ": ["LH", "SIRI", "SPALI", "AP", "ORI", "QH"],
    "⛽ แก๊งค์พลังงาน & สาธารณูปโภค": ["PTT", "BCP", "TTW", "EGCO", "RATCH", "EASTW"],
    "📡 แก๊งค์โครงสร้างพื้นฐาน (Defensive)": ["ADVANC", "INTUCH", "DIF", "JASIF"],
    "🏥 แก๊งค์โรงพยาบาล (Growth+Defensive)": ["BDMS", "BH", "BCH"],
    "🛒 แก๊งค์ค้าปลีก & อาหาร": ["CPALL", "HMPRO", "TU", "TVO"]
}

# ==========================================
# 3. ส่วนแสดงผล (UI)
# ==========================================
st.title("💎 Buffett Value Scanner")
st.caption("เครื่องมือสแกนหุ้นพื้นฐานดี (Value Investing) ฉบับวอร์เรน บัฟเฟตต์")

# --- ส่วนเลือกหุ้น (Menu Selection) ---
with st.container():
    st.subheader("🎯 เลือกเป้าหมายลงทุน")
    col_cat, col_stock = st.columns(2)
    
    with col_cat:
        category = st.selectbox("หมวดหมู่หุ้นคุณค่า", list(value_stocks.keys()))
    
    with col_stock:
        # Logic การเลือกหุ้น
        if category == "พิมพ์เอง (Custom)":
            selected_symbol = st.text_input("ระบุชื่อหุ้นเอง", "").upper()
        else:
            selected_symbol = st.selectbox("เลือกหุ้นในกลุ่ม", value_stocks[category])

    st.write("") # เว้นบรรทัด
    btn_scan = st.button("🔍 ตรวจสุขภาพหุ้น")

# ==========================================
# 4. ส่วนประมวลผล (Engine)
# ==========================================
if btn_scan and selected_symbol:
    # จัดการชื่อหุ้น
    symbol = selected_symbol.replace(".BK", "").upper()

    with st.spinner(f"⏳ กำลังเจาะงบการเงิน {symbol}..."):
        try:
            # ดึงข้อมูลจาก Yahoo Finance
            ticker_name = f"{symbol}.BK"
            stock = yf.Ticker(ticker_name)
            info = stock.info
            
            # --- ดึงตัวเลขสำคัญ (Data Extraction) ---
            price = info.get('currentPrice', 0)
            pe = info.get('trailingPE', 0)
            pbv = info.get('priceToBook', 0)
            roe = (info.get('returnOnEquity', 0) or 0) * 100
            
            # แก้บั๊กปันผล (Smart Logic)
            raw_div = info.get('dividendYield', 0) or 0
            if raw_div > 1: 
                div_yield = raw_div 
            else:
                div_yield = raw_div * 100

            # --- ส่วนแสดงผล ---
            st.divider()
            st.markdown(f"### 📊 ผลตรวจร่างกาย: {symbol}")
            st.markdown(f"<p class='big-font'>ราคาปัจจุบัน: {price:.2f} บาท</p>", unsafe_allow_html=True)
            
            # แสดงเกจวัดพลัง 3 ด้าน
            c1, c2, c3 = st.columns(3)
            
            # 1. ความถูกแพง (P/E)
            with c1:
                st.write("💰 **ความถูก (P/E)**")
                if 0 < pe <= 15:
                    st.success(f"{pe:.2f}\n(ถูก)")
                    s1 = 1
                elif 15 < pe <= 25:
                    st.warning(f"{pe:.2f}\n(กลาง)")
                    s1 = 0.5
                else:
                    st.error(f"{pe:.2f}\n(แพง)")
                    s1 = 0
            
            # 2. เงินปันผล (Dividend)
            with c2:
                st.write("🎁 **ปันผล (Yield)**")
                if div_yield >= 5: 
                    st.success(f"{div_yield:.2f}%\n(งาม)")
                    s2 = 1
                elif 3 <= div_yield < 5:
                    st.warning(f"{div_yield:.2f}%\n(พอใช้)")
                    s2 = 0.5
                else:
                    st.error(f"{div_yield:.2f}%\n(น้อย)")
                    s2 = 0
                    
            # 3. ความเก่ง (ROE)
            with c3:
                st.write("🚀 **ความเก่ง (ROE)**")
                if roe >= 15:
                    st.success(f"{roe:.2f}%\n(เทพ)")
                    s3 = 1
                elif 10 <= roe < 15:
                    st.warning(f"{roe:.2f}%\n(เก่ง)")
                    s3 = 0.5
                else:
                    st.error(f"{roe:.2f}%\n(เฉยๆ)")
                    s3 = 0

            st.divider()
            
            # --- สรุปเกรด (Final Verdict) ---
            total_score = s1 + s2 + s3
            
            if total_score >= 2.5:
                st.balloons()
                st.markdown(f"""
                <div class="success-box">
                    <h3>💎 GRADE A (คะแนน {total_score}/3)</h3>
                    <p><b>"หุ้นเพชรในตม!"</b> พื้นฐานแกร่ง ราคาถูก ปันผลหนัก<br>
                    ✅ <b>Action:</b> เหมาะสำหรับซื้อเก็บกินยาว (DCA) / ช้อนซื้อลงทุน</p>
                </div>
                """, unsafe_allow_html=True)
            elif total_score >= 1.5:
                st.markdown(f"""
                <div class="warning-box">
                    <h3>🥇 GRADE B (คะแนน {total_score}/3)</h3>
                    <p><b>"หุ้นดีน่าคบ"</b> พื้นฐานผ่านเกณฑ์ แต่อาจมีบางจุดที่ต้องดูเพิ่ม<br>
                    ⚠️ <b>Action:</b> ทยอยสะสมได้เมื่อราคาย่อตัว</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="error-box">
                    <h3>💀 GRADE C (คะแนน {total_score}/3)</h3>
                    <p><b>"มีความเสี่ยง"</b> ราคาแพงไป หรือ ปันผลน้อยไป<br>
                    ❌ <b>Action:</b> ควรหลีกเลี่ยง หรือศึกษาให้ลึกกว่านี้</p>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"❌ ไม่พบข้อมูลหุ้น {symbol} หรือตลาดหลักทรัพย์ยังไม่ส่งงบมาครับ")

elif btn_scan and not selected_symbol:
    st.warning("⚠️ กรุณาเลือกหุ้นก่อนครับ")
