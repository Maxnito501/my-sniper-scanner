import streamlit as st
import pandas as pd
import os
import datetime

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Project TITAN HQ",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 🎨 ปรับแต่ง CSS (ฟอนต์ Kanit + เมนูสวย) ---
st.markdown("""
<style>
    /* นำเข้าฟอนต์ Kanit */
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');

    /* บังคับใช้ฟอนต์ Kanit ทั้งแอป */
    html, body, [class*="css"], [data-testid="stSidebar"] {
        font-family: 'Kanit', sans-serif !important;
    }

    /* ตกแต่ง Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 2px solid #e9ecef;
    }

    /* ตกแต่งตัวหนังสือในเมนู */
    div[data-testid="stSidebarNav"] li div a {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #0f172a !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    
    /* ปรับขนาดไอคอน Emoji ในเมนู */
    div[data-testid="stSidebarNav"] li div a span {
        font-size: 20px !important;
        margin-right: 10px !important;
    }

    /* ตกแต่ง Header หลัก */
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Footer ด้านล่าง */
    .footer {
        text-align: center;
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px dashed #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ส่วนแสดงผลหลัก (Sidebar) ---
st.sidebar.title("🎛️ Control Panel")
st.sidebar.info(f"👤 ผู้ใช้งาน: **วิศวกรโบ้**\n🚀 สถานะ: **Super Admin**")

# --- 4. ส่วนเนื้อหา (Main Content) ---
st.title("🏗️ Project TITAN: The Wealth Commander")
st.markdown(f"##### **ยินดีต้อนรับครับวิศวกร!** (วันที่: {datetime.date.today().strftime('%d/%m/%Y')})")
st.write("---")

# --- เมนูนำทาง (Updated: 6 รายการ) ---
st.markdown("""
### 🚀 เลือกห้องปฏิบัติการ (เมนูซ้ายมือ):
* **🧭 Polaris:** เรดาร์สแกนหุ้นและกองทุน (Sniper Mode)
* **🛡️ Titan:** บัญชีทรัพย์สินและแผนเกษียณ (Asset Manager)
* **📅 DCA Planner:** ปฏิทินหาของถูก & Oracle จับจังหวะ
* **🥈 Gold vs Silver:** เปรียบเทียบราคาทองและเงิน
* **🛰️ Gold Sniper:** ระบบเทรดทองคำระยะสั้น (แบ่งไม้-ไล่ราคา)
* **⚖️ Tech vs Quality:** เครื่องมือชั่งน้ำหนักกองทุน EDCA (Semi vs Quality) 🆕
""")

st.write("")
st.write("")

# --- Footer ---
st.markdown("<div class='footer'>Created by <b>โบ้ 50</b></div>", unsafe_allow_html=True)
