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

# --- 2. 🎨 ปรับแต่ง CSS (ฉบับอัปเกรด V2: บังคับฟอนต์เมนู) ---
st.markdown("""
<style>
    /* นำเข้าฟอนต์ Kanit */
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');

    /* 1. บังคับฟอนต์ทั้งแอป */
    html, body, [class*="css"], [data-testid="stSidebar"] {
        font-family: 'Kanit', sans-serif !important;
    }

    /* 2. ตกแต่งพื้นหลัง Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 2px solid #e9ecef;
    }

    /* 3. เจาะจงแก้ตัวหนังสือในเมนู (Navigation) ให้ใหญ่และชัด */
    div[data-testid="stSidebarNav"] li div a {
        font-size: 18px !important;     /* ขนาดตัวอักษรเมนู */
        font-weight: 600 !important;    /* ความหนา */
        color: #0f172a !important;      /* สีตัวอักษร (ดำอมน้ำเงิน) */
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    
    /* แก้ไอคอน Emoji ในเมนูให้ใหญ่ตาม */
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
    
    .footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px dashed #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ส่วนแสดงผลหลัก ---
st.sidebar.title("🎛️ Control Panel")
st.sidebar.info(f"👤 ผู้ใช้งาน: **วิศวกรโบ้**\n🚀 สถานะ: **Super Admin**")

st.title("🏗️ Project TITAN: The Wealth Commander")
st.markdown(f"##### **ยินดีต้อนรับครับวิศวกร!** (วันที่: {datetime.date.today().strftime('%d/%m/%Y')})")
st.write("---")

# --- เช็คระบบฐานข้อมูล ---
csv_file = 'assets.csv'
if not os.path.exists(csv_file):
    st.info("💡 เริ่มต้นใช้งานโดยไปที่เมนู **Titan** ด้านซ้าย เพื่อบันทึกทรัพย์สินครับ")

# --- Dashboard สรุปยอดเงิน ---
if os.path.exists(csv_file):
    try:
        df = pd.read_csv(csv_file)
        if 'Value (THB)' in df.columns:
            total_wealth = df['Value (THB)'].sum()
            if not df.empty:
                top_asset_row = df.loc[df['Value (THB)'].idxmax()]
                top_asset_name = top_asset_row['Category']
            else:
                top_asset_name = "-"
            
            # KPI Cards
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style="background-color:#dbeafe; padding:20px; border-radius:12px; text-align:center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <h4 style="margin:0; color:#1e40af; font-size:1rem;">💰 ความมั่งคั่งสุทธิ</h4>
                    <h2 style="margin:5px 0 0 0; color:#1e3a8a; font-size:1.8rem;">{total_wealth:,.0f} ฿</h2>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background-color:#d1fae5; padding:20px; border-radius:12px; text-align:center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <h4 style="margin:0; color:#065f46; font-size:1rem;">🏆 สินทรัพย์หลัก</h4>
                    <h2 style="margin:5px 0 0 0; color:#064e3b; font-size:1.5rem;">{top_asset_name}</h2>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style="background-color:#f3f4f6; padding:20px; border-radius:12px; text-align:center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <h4 style="margin:0; color:#374151; font-size:1rem;">📈 สถานะระบบ</h4>
                    <h2 style="margin:5px 0 0 0; color:#111827; font-size:1.8rem;">Online ✅</h2>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ ไฟล์ข้อมูลไม่สมบูรณ์")
    except Exception as e:
        st.warning(f"⚠️ กำลังประมวลผล... ({e})")

st.write("---")
st.markdown("""
### 🚀 เลือกห้องปฏิบัติการ:
* **🧭 Polaris:** เรดาร์สแกนหุ้นและกองทุน
* **🛡️ Titan:** บัญชีทรัพย์สินและแผนเกษียณ
* **📅 DCA Planner:** ปฏิทินหาของถูก
* **🥈 Gold vs Silver:** เปรียบเทียบราคาทองและเงิน
""")

# Footer
st.markdown("<div class='footer'>Engineered by <b>โบ้ 50</b> | Powered by Python & Streamlit</div>", unsafe_allow_html=True)
