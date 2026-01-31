import streamlit as st
import pandas as pd
import os
import datetime

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Project TITAN HQ",
    page_icon="🏗️",
    layout="wide"
)

# --- Header ---
st.title("🏗️ Project TITAN: The Wealth Commander")
st.markdown(f"**ยินดีต้อนรับครับวิศวกรโบ้!** (วันที่: {datetime.date.today().strftime('%d/%m/%Y')})")
st.write("---")

# --- เช็คยอดเงินรวมจาก Database ---
csv_file = 'assets.csv'
if os.path.exists(csv_file):
    try:
        df = pd.read_csv(csv_file)
        # เช็คคอลัมน์และคำนวณ
        if 'Value (THB)' in df.columns:
            total_wealth = df['Value (THB)'].sum()
            
            # หา Asset ที่ใหญ่ที่สุด
            top_asset_row = df.loc[df['Value (THB)'].idxmax()]
            top_asset_name = top_asset_row['Category']
            
            # แสดง Dashboard ย่อๆ (KPI Cards)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="💰 ความมั่งคั่งสุทธิ (Net Worth)", value=f"{total_wealth:,.0f} ฿")
            with col2:
                st.metric(label="🏆 สินทรัพย์ก้อนใหญ่สุด", value=f"{top_asset_name}")
            with col3:
                st.metric(label="📈 สถานะระบบ", value="Online ✅")
        else:
            st.warning("⚠️ ไฟล์ข้อมูลไม่สมบูรณ์ (ขาดคอลัมน์ Value)")
            
    except Exception as e:
        st.warning(f"⚠️ กำลังประมวลผลฐานข้อมูล... ({e})")
else:
    st.info("💡 เริ่มต้นใช้งานโดยไปที่เมนู **Titan** ด้านซ้าย เพื่อบันทึกทรัพย์สินครับ")

st.write("---")
st.markdown("""
### 🚀 เลือกห้องปฏิบัติการ (เมนูซ้ายมือ):
1.  **🧭 Polaris:** เรดาร์สแกนหุ้นและกองทุน (Sniper Mode)
2.  **🛡️ Titan:** ห้องบัญชีและวางแผนเกษียณ (Asset Manager)
3.  **📅 DCA Planner:** ปฏิทินหาของถูก
4.  **🥈 Gold vs Silver:** เปรียบเทียบราคาทองและเงิน
""")
