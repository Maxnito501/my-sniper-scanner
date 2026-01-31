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

# --- 2. 🎨 ปรับแต่ง CSS (ฟอนต์ + กราฟิกเมนูซ้าย) ---
st.markdown("""
<style>
    /* นำเข้าฟอนต์ Kanit จาก Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');

    /* บังคับใช้ฟอนต์ Kanit ทั้งแอป */
    html, body, [class*="css"]  {
        font-family: 'Kanit', sans-serif;
    }

    /* ตกแต่ง Sidebar (เมนูซ้าย) */
    [data-testid="stSidebar"] {
        background-image: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        border-right: 2px solid #dee2e6;
    }

    /* ตกแต่งชื่อเมนูใน Sidebar */
    [data-testid="stSidebarNav"] span {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #1e40af; /* สีน้ำเงินเข้ม */
        padding-top: 5px;
        padding-bottom: 5px;
    }

    /* ตกแต่ง Header */
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* กล่องข้อความด้านล่าง */
    .footer {
        text-align: center;
        color: #64748b;
        font-size: 0.8rem;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ส่วนแสดงผลหลัก ---

# เพิ่มโลโก้หรือรูปภาพที่ Sidebar (ถ้ามี URL รูป)
# st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2555/2555013.png", width=100)
st.sidebar.title("🎛️ Control Panel")
st.sidebar.info(f"ผู้ใช้งาน: **วิศวกรโบ้**\nสถานะ: **Super Admin**")

st.title("🏗️ Project TITAN: The Wealth Commander")
st.markdown(f"##### **ยินดีต้อนรับครับวิศวกร!** (วันที่: {datetime.date.today().strftime('%d/%m/%Y')})")
st.write("---")

# --- เช็คระบบฐานข้อมูล (เบื้องหลัง) ---
csv_file = 'assets.csv'
if not os.path.exists(csv_file):
    st.info("💡 เริ่มต้นใช้งานโดยไปที่เมนู **Titan** ด้านซ้าย เพื่อบันทึกทรัพย์สินครับ")

# --- Dashboard สรุปยอดเงิน (ถ้ามีข้อมูล) ---
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
            
            # KPI Cards แบบมีสีสัน
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style="background-color:#dbeafe; padding:15px; border-radius:10px; text-align:center;">
                    <h4 style="margin:0; color:#1e40af;">💰 ความมั่งคั่งสุทธิ</h4>
                    <h2 style="margin:0; color:#1e3a8a;">{total_wealth:,.0f} ฿</h2>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background-color:#d1fae5; padding:15px; border-radius:10px; text-align:center;">
                    <h4 style="margin:0; color:#065f46;">🏆 สินทรัพย์หลัก</h4>
                    <h2 style="margin:0; color:#064e3b;">{top_asset_name}</h2>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style="background-color:#f3f4f6; padding:15px; border-radius:10px; text-align:center;">
                    <h4 style="margin:0; color:#374151;">📈 สถานะระบบ</h4>
                    <h2 style="margin:0; color:#111827;">Online ✅</h2>
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
```

### 🎨 สิ่งที่เปลี่ยนแปลง (Design Upgrade)
1.  **ฟอนต์ใหม่ (Kanit):** เปลี่ยนจากฟอนต์เดิมๆ เป็นฟอนต์ **"Kanit"** (คณิต) ที่ดูทันสมัยและอ่านง่าย เหมาะกับ Dashboard ภาษาไทย
2.  **Sidebar ไล่เฉดสี:** พื้นหลังเมนูซ้ายจะไม่ใช่สีขาวเรียบๆ แต่จะไล่เฉดสีเทาอ่อนๆ ให้ดูมีมิติ
3.  **ขนาดตัวหนังสือเมนู:** ผมปรับให้ตัวหนังสือเมนูทางซ้าย **"ใหญ่ขึ้นและหนาขึ้น"** (Bold) จะได้จิ้มง่ายๆ ในมือถือ
4.  **KPI Cards:** ปรับกล่องแสดงยอดเงินให้มีสีพื้นหลัง (ฟ้า/เขียว) ดูแยกส่วนชัดเจน

ลองกดรันดูครับวิศวกรโบ้! หน้าตาแอปจะดู **"แพง"** ขึ้นมาทันทีครับ! 😎✨

*(หมายเหตุ: เพื่อให้ฟอนต์สวยแบบนี้ทุกหน้า แนะนำให้ก๊อปปี้ท่อน `<style>...</style>` ไปแปะไว้ส่วนบนสุดของไฟล์ใน folder `pages` ด้วยนะครับ)*
