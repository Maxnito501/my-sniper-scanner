import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="My Portfolio Status", page_icon="📊", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
    
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 5px solid #1e3a8a;
    }
    .big-money {
        font-size: 2.5rem;
        font-weight: bold;
        color: #15803d;
    }
    .category-header {
        background-color: #f1f5f9;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 My Portfolio: ผลลัพธ์แห่งวินัย 20 ปี")
st.markdown("**สรุปสถานะพอร์ตการลงทุนแยกตามกลยุทธ์ (Strategic Allocation)**")
st.write("---")

# --- 2. ระบบจัดการข้อมูล (Database) ---
DB_FILE = 'my_portfolio.json'

DEFAULT_DATA = {
    "1. กองหลัง (Defensive)": [],  # กบข., สหกรณ์
    "2. ตัวรุก (Aggressive)": [],  # หุ้นซิ่ง, Sniper
    "3. หุ้นปันผล (Dividend)": [], # หุ้นไทยพื้นฐาน
    "4. กองทุนภาษี (Tax Saving)": [], # RMF, SSF, ThaiESG
    "5. กองทุนระยะยาว (Long-term)": [], # กองทุนเปิดทั่วไป
    "6. ประกัน (Insurance)": []    # แยกต่างหาก
}

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return DEFAULT_DATA

def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if 'my_port_data' not in st.session_state:
    st.session_state.my_port_data = load_data()

# --- 3. Sidebar: เพิ่ม/ลบ รายการ ---
st.sidebar.header("📝 บันทึกรายการ")
category = st.sidebar.selectbox("เลือกหมวดหมู่", list(DEFAULT_DATA.keys()))

with st.sidebar.form("add_asset_form"):
    asset_name = st.text_input("ชื่อรายการ (เช่น กบข., PTT, SCBSEMI)")
    
    input_type = st.radio("วิธีระบุวิศวกร:", ["ใส่ยอดเงินรวม", "คำนวณ (จำนวน x ราคา)"])
    
    val = 0.0
    if input_type == "ใส่ยอดเงินรวม":
        val = st.number_input("มูลค่าปัจจุบัน (บาท)", min_value=0.0, step=1000.0)
    else:
        qty = st.number_input("จำนวนหน่วย/หุ้น", min_value=0.0, step=1.0)
        price = st.number_input("ราคาต่อหน่วย/หุ้น", min_value=0.0, step=0.1)
        val = qty * price
        st.markdown(f"**รวมเป็นเงิน: {val:,.2f} บาท**")

    submitted = st.form_submit_button("💾 บันทึกรายการ")
    
    if submitted and asset_name and val > 0:
        # เช็คว่ามีรายการนี้อยู่แล้วไหม (ถ้ามีให้ทับ)
        existing = next((item for item in st.session_state.my_port_data[category] if item['name'] == asset_name), None)
        if existing:
            existing['value'] = val
        else:
            st.session_state.my_port_data[category].append({'name': asset_name, 'value': val})
        
        save_data(st.session_state.my_port_data)
        st.success("บันทึกเรียบร้อย!")
        st.rerun()

# ปุ่มลบรายการ
with st.sidebar.expander("🗑️ ลบรายการ"):
    del_cat = st.selectbox("หมวดหมู่ที่จะลบ", list(DEFAULT_DATA.keys()), key='del_cat')
    items = [item['name'] for item in st.session_state.my_port_data[del_cat]]
    del_item = st.selectbox("เลือกรายการ", items, key='del_item')
    
    if st.button("ลบรายการนี้"):
        st.session_state.my_port_data[del_cat] = [i for i in st.session_state.my_port_data[del_cat] if i['name'] != del_item]
        save_data(st.session_state.my_port_data)
        st.rerun()

# --- 4. คำนวณและเตรียมข้อมูล ---
portfolio_data = []
insurance_total = 0
investment_total = 0

for cat, items in st.session_state.my_port_data.items():
    cat_sum = 0
    for item in items:
        cat_sum += item['value']
        if "ประกัน" in cat:
            insurance_total += item['value']
        else:
            investment_total += item['value']
            # เตรียมข้อมูลสำหรับกราฟ (ไม่เอาประกัน)
            portfolio_data.append({'Category': cat, 'Asset': item['name'], 'Value': item['value']})

total_wealth = investment_total + insurance_total

# --- 5. Dashboard แสดงผล ---

# KPI Cards
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <h4>💰 ความมั่งคั่งสุทธิ (Net Worth)</h4>
        <div class="big-money">{total_wealth:,.0f} ฿</div>
        <small>รวมทุกอย่างในชีวิต</small>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #10b981;">
        <h4>📈 พอร์ตลงทุน (Investment)</h4>
        <div class="big-money" style="color: #10b981;">{investment_total:,.0f} ฿</div>
        <small>เงินที่ทำงานให้เรา</small>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #f59e0b;">
        <h4>🛡️ หลักประกัน (Insurance)</h4>
        <div class="big-money" style="color: #f59e0b;">{insurance_total:,.0f} ฿</div>
        <small>ความคุ้มครองชีวิต/สุขภาพ</small>
    </div>
    """, unsafe_allow_html=True)

st.write("---")

# --- 6. กราฟและการวิเคราะห์ ---
if investment_total > 0:
    col_chart, col_detail = st.columns([1.5, 1])

    with col_chart:
        st.subheader("🧩 โครงสร้างพอร์ตลงทุน (Sunburst)")
        df_chart = pd.DataFrame(portfolio_data)
        fig = px.sunburst(
            df_chart, 
            path=['Category', 'Asset'], 
            values='Value',
            color='Category',
            color_discrete_map={
                "1. กองหลัง (Defenders)": "#1e3a8a",
                "2. ตัวรุก (Attackers)": "#ef4444",
                "3. หุ้นปันผล (Dividend)": "#10b981",
                "4. กองทุนภาษี (Tax Saving)": "#f59e0b",
                "5. กองทุนระยะยาว (Long-term)": "#3b82f6"
            }
        )
        fig.update_traces(textinfo="label+percent entry")
        fig.update_layout(height=500, margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_detail:
        st.subheader("📋 รายละเอียดพอร์ต")
        
        # วนลูปแสดง Progress Bar ของแต่ละหมวด
        cats = [k for k in DEFAULT_DATA.keys() if "ประกัน" not in k]
        for cat in cats:
            items = st.session_state.my_port_data[cat]
            if items:
                sub_total = sum(i['value'] for i in items)
                pct = (sub_total / investment_total) * 100
                st.markdown(f"**{cat}** : {sub_total:,.0f} ฿ ({pct:.1f}%)")
                st.progress(min(pct/100, 1.0))
                # แสดงรายการย่อยแบบ Expander
                with st.expander("ดูไส้ใน"):
                    for i in items:
                        st.write(f"- {i['name']}: {i['value']:,.0f} ฿")
    
    # --- 7. บทวิเคราะห์จากวิศวกร (Engineer's Insight) ---
    st.write("---")
    st.info("""
    ### 👷‍♂️ Engineer's Note:
    * **ความสมดุล:** ลองดูที่กราฟวงกลมครับ ถ้าสีน้ำเงินเข้ม (กองหลัง) กินพื้นที่ประมาณ 50-60% แสดงว่าฐานรากแน่นปึ้กครับ
    * **ประสิทธิภาพ:** ส่วนสีแดง (ตัวรุก) และสีเขียว (ปันผล) คือส่วนที่จะช่วยชนะเงินเฟ้อ ถ้ามีรวมกันสัก 30-40% ถือว่าเครื่องยนต์แรงดีครับ
    * **ความพอใจ:** ตัวเลขเหล่านี้ไม่ได้มาเพราะโชคช่วย แต่มาจาก **"วินัย 20 ปี"** ของคุณโบ้เองครับ ภูมิใจได้เลย! 🏆
    """)

else:
    st.info("👈 กรุณาเพิ่มข้อมูลสินทรัพย์ที่แถบด้านซ้าย เพื่อเริ่มสร้าง Dashboard แห่งความภาคภูมิใจครับ")

# Footer
st.markdown("<div style='text-align: center; color: grey; margin-top: 50px;'>🛠️ Engineered by <b>โบ้ 50</b></div>", unsafe_allow_html=True)
