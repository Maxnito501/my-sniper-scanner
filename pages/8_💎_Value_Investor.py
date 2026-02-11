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
# 2. ส่วนแสดงผล (UI)
# ==========================================
st.title("💎 Buffett Value Scanner")
st.caption("เครื่องมือสแกนหุ้นพื้นฐานดี (Value Investing) ฉบับวอร์เรน บัฟเฟตต์")

with st.container():
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        symbol = st.text_input("ป้อนชื่อหุ้น (เช่น TISCO, PTT, LH)", placeholder="ชื่อหุ้น...").upper()
    with col_btn:
        st.write("") # ดันปุ่มลงมานิดนึง
        st.write("") 
        btn_scan = st.button("🔍 ตรวจสุขภาพ")

# ==========================================
# 3. ส่วนประมวลผล (Engine)
# ==========================================
if btn_scan and symbol:
    with st.spinner(f"⏳ กำลังเจาะงบการเงิน {symbol}..."):
        try:
            # ดึงข้อมูลจาก Yahoo Finance
            ticker_name = f"{symbol}.BK" if not symbol.endswith(".BK") else symbol
            stock = yf.Ticker(ticker_name)
            info = stock.info
            
            # --- ดึงตัวเลขสำคัญ (Data Extraction) ---
            price = info.get('currentPrice', 0)
            pe = info.get('trailingPE', 0)
            pbv = info.get('priceToBook', 0)
            roe = (info.get('returnOnEquity', 0) or 0) * 100
            
            # ** แก้บั๊กปันผลตรงนี้ครับ (Smart Logic) **
            raw_div = info.get('dividendYield', 0) or 0
            if raw_div > 1: 
                # ถ้าค่าดิบมาเกิน 1 แสดงว่าเป็น % อยู่แล้ว (เช่น 7.5) ไม่ต้องคูณ
                div_yield = raw_div 
            else:
                # ถ้าค่าดิบมาเป็นทศนิยม (เช่น 0.075) ให้คูณ 100
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
                if div_yield >= 5: # ปรับเกณฑ์ให้เข้มขึ้นสำหรับสายปันผล
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
                    ✅ เหมาะสำหรับ: <b>ซื้อเก็บกินยาว (DCA) / ช้อนซื้อลงทุน</b></p>
                </div>
                """, unsafe_allow_html=True)
            elif total_score >= 1.5:
                st.markdown(f"""
                <div class="warning-box">
                    <h3>🥇 GRADE B (คะแนน {total_score}/3)</h3>
                    <p><b>"หุ้นดีน่าคบ"</b> พื้นฐานผ่านเกณฑ์ แต่อาจมีบางจุดที่ต้องดูเพิ่ม<br>
                    ⚠️ คำแนะนำ: <b>ทยอยสะสมได้เมื่อราคาย่อตัว</b></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="error-box">
                    <h3>💀 GRADE C (คะแนน {total_score}/3)</h3>
                    <p><b>"มีความเสี่ยง"</b> ราคาแพงไป หรือ ปันผลน้อยไป<br>
                    ❌ คำแนะนำ: <b>ควรหลีกเลี่ยง หรือศึกษาให้ลึกกว่านี้</b></p>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"❌ ไม่พบข้อมูลหุ้น {symbol} หรือตลาดหลักทรัพย์ยังไม่ส่งงบมาครับ (Error: {e})")

elif btn_scan and not symbol:
    st.warning("⚠️ กรุณากรอกชื่อหุ้นก่อนกดปุ่มครับ")
