import streamlit as st
import pandas as pd

# --- Configuration ---
st.set_page_config(
    page_title="Suchat Pro Sniper (Dime! Edition)",
    page_icon="🎯",
    layout="wide"
)

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #020617;
    }
    .stMetric {
        background-color: #0f172a;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #1e293b;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #0f172a;
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- App Logic & Calculations ---
DIME_COMMISSION = 0.0015
VAT = 0.07
REGULATORY_FEE = 0.00007

def calculate_net_profit(buy_price, sell_price, shares):
    buy_gross = buy_price * shares
    sell_gross = sell_price * shares
    
    # Fees for both buy and sell sides
    buy_fees = (buy_gross * DIME_COMMISSION) + (buy_gross * DIME_COMMISSION * VAT) + (buy_gross * REGULATORY_FEE)
    sell_fees = (sell_gross * DIME_COMMISSION) + (sell_gross * DIME_COMMISSION * VAT) + (sell_gross * REGULATORY_FEE)
    
    total_fees = buy_fees + sell_fees
    gross_profit = sell_gross - buy_gross
    net_profit = gross_profit - total_fees
    return net_profit, total_fees

# --- Sidebar / Header Status ---
st.title("🎯 SUCHAT PRO SNIPER")
st.caption("Dime! Integration • Engineering Edition v2.1 (Streamlit Version)")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("เงินในพอร์ต (Dime!)", "฿20,172.03", "172.03 Today")
with col2:
    st.metric("เงินสต็อกสำรอง", "฿40,000.00")
with col3:
    st.metric("ความแม่นยำ AI", "78.5%")
with col4:
    st.metric("LINE Status", "Connected", delta_color="normal")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Top 15 Sniper", "🛡️ พอร์ตแม่ทัพ", "🧮 เครื่องคิดเลข Dime!", "📜 ประวัติกำไร"])

with tab1:
    st.subheader("TOP 15 STRATEGIC SNIPER WATCHLIST")
    st.info("💡 แผนที่การรบ: รายชื่อหุ้น 15 ตัวที่ควรเฝ้าระวัง พี่โบ้เช็กกับเรดาร์ต่อได้เลยครับ")
    
    # Mock Data based on your strategy
    data = [
        {"หุ้น": "WHA", "กลุ่ม": "นิคมฯ", "ราคา": 4.12, "Entry": 4.10, "Target": 4.30, "Stop": 4.02, "Status": "Hot"},
        {"หุ้น": "TRUE", "กลุ่ม": "สื่อสาร", "ราคา": 12.30, "Entry": 12.20, "Target": 13.00, "Stop": 11.90, "Status": "Strong"},
        {"หุ้น": "SIRI", "กลุ่ม": "อสังหาฯ", "ราคา": 1.82, "Entry": 1.80, "Target": 1.95, "Stop": 1.76, "Status": "Zing"},
        {"หุ้น": "DOHOME", "กลุ่ม": "ก่อสร้าง", "ราคา": 10.50, "Entry": 10.40, "Target": 11.50, "Stop": 10.10, "Status": "Breakout"},
        {"หุ้น": "CPALL", "กลุ่ม": "ค้าปลีก", "ราคา": 65.25, "Entry": 64.50, "Target": 68.00, "Stop": 63.50, "Status": "Steady"},
        {"หุ้น": "AMATA", "กลุ่ม": "นิคมฯ", "ราคา": 28.50, "Entry": 28.00, "Target": 31.00, "Stop": 27.25, "Status": "Strong"},
        {"หุ้น": "GLOBAL", "กลุ่ม": "ก่อสร้าง", "ราคา": 16.80, "Entry": 16.50, "Target": 18.20, "Stop": 16.10, "Status": "Steady"},
        {"หุ้น": "DELTA", "กลุ่ม": "เทค", "ราคา": 152.00, "Entry": 150.00, "Target": 165.00, "Stop": 145.00, "Status": "Super Zing"},
    ]
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("COMMANDER CORE (หุ้นเสาเข็ม)")
    p_col1, p_col2 = st.columns([2, 1])
    
    with p_col1:
        st.write("รายการหุ้นในพอร์ตปัจจุบัน")
        port_data = [
            {"หุ้น": "TISCO", "จำนวน": 100, "ทุน": 112.50, "ปัจจุบัน": 112.50, "กำไร/ขาดทุน": "0.00%"},
            {"หุ้น": "SCB", "จำนวน": 25, "ทุน": 135.50, "ปัจจุบัน": 139.50, "กำไร/ขาดทุน": "+2.95%"},
        ]
        st.table(port_data)
    
    with p_col2:
        st.markdown("""
        ### บทวิเคราะห์วิศวกร
        พี่โบ้ครับ! พอร์ตพี่ตอนนี้เป็นสัดส่วน **เสาเข็มปันผล 75%** และ **กระสุนซิ่ง 25%** มั่นคงแต่ยังทำรอบได้ เหมาะสำหรับสะสมเงินทุนขอหลักแสนครับ
        """)
        if st.button("เติมเงินจากสต็อก 40K", use_container_width=True):
            st.success("ส่งคำสั่งเติมเงินเรียบร้อย!")

with tab3:
    st.subheader("DIME! NET CALCULATOR")
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        symbol = st.text_input("ชื่อหุ้น", "WHA")
        shares = st.number_input("จำนวนหุ้น", value=5000, step=100)
    with c_col2:
        buy_p = st.number_input("ราคาซื้อ (Buy)", value=4.10, format="%.2f")
        sell_p = st.number_input("ราคาขาย (Sell)", value=4.20, format="%.2f")
    
    net_profit, fees = calculate_net_profit(buy_p, sell_p, shares)
    
    st.divider()
    res_col1, res_col2 = st.columns(2)
    res_col1.metric("กำไรสุทธิ (เข้ากระเป๋า)", f"฿{net_profit:,.2f}")
    res_col2.metric("ค่าธรรมเนียม Dime! รวม", f"฿{fees:,.2f}", delta_color="inverse")

with tab4:
    st.subheader("PROFIT HISTORY (บันทึกชัยชนะ)")
    st.success("**12 ก.พ. 26:** GPSC + WHA (Zing Run) | กำไรสุทธิ +฿172.03")
    
    st.info("เตรียมล่าค่ากับข้าววันพรุ่งนี้... เป้าหมาย ฿300.00")
    
    st.divider()
    st.write("### สรุปกำไรสะสมเดือนนี้")
    st.title("฿172.03")
    st.progress(0.57, text="57% ของเป้าหมาย ฿300")

st.divider()
st.caption("© 2026 SUCHAT ENGINEERING TRADING SYSTEM • EXCLUSIVELY FOR P'BO")
