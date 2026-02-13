import streamlit as st
import pandas as pd
import random

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
    buy_fees = (buy_gross * DIME_COMMISSION) + (buy_gross * DIME_COMMISSION * VAT) + (buy_gross * REGULATORY_FEE)
    sell_fees = (sell_gross * DIME_COMMISSION) + (sell_gross * DIME_COMMISSION * VAT) + (sell_gross * REGULATORY_FEE)
    total_fees = buy_fees + sell_fees
    gross_profit = sell_gross - buy_gross
    net_profit = gross_profit - total_fees
    return net_profit, total_fees

# --- Simulation for "Auto Scan" ---
def get_scanned_data(num_items):
    # รายชื่อหุ้นใน 6 กลุ่มยุทธศาสตร์ของพี่โบ้
    stocks_pool = [
        {"หุ้น": "WHA", "กลุ่ม": "นิคมฯ", "Entry": 4.10, "Target": 4.30, "Stop": 4.02},
        {"หุ้น": "AMATA", "กลุ่ม": "นิคมฯ", "Entry": 28.00, "Target": 31.00, "Stop": 27.25},
        {"หุ้น": "ROJNA", "กลุ่ม": "นิคมฯ", "Entry": 7.10, "Target": 7.80, "Stop": 6.95},
        {"หุ้น": "TRUE", "กลุ่ม": "สื่อสาร", "Entry": 12.20, "Target": 13.00, "Stop": 11.90},
        {"หุ้น": "ADVANC", "กลุ่ม": "สื่อสาร", "Entry": 242.00, "Target": 255.00, "Stop": 238.00},
        {"หุ้น": "DELTA", "กลุ่ม": "เทค", "Entry": 150.00, "Target": 165.00, "Stop": 145.00},
        {"หุ้น": "HANA", "กลุ่ม": "เทค", "Entry": 41.50, "Target": 45.00, "Stop": 40.50},
        {"หุ้น": "GULF", "กลุ่ม": "เทค/พลังงาน", "Entry": 54.00, "Target": 58.00, "Stop": 53.00},
        {"หุ้น": "SIRI", "กลุ่ม": "อสังหาฯ", "Entry": 1.80, "Target": 1.95, "Stop": 1.76},
        {"หุ้น": "AP", "กลุ่ม": "อสังหาฯ", "Entry": 10.70, "Target": 11.50, "Stop": 10.40},
        {"หุ้น": "SPALI", "กลุ่ม": "อสังหาฯ", "Entry": 19.50, "Target": 21.00, "Stop": 19.20},
        {"หุ้น": "DOHOME", "กลุ่ม": "ก่อสร้าง", "Entry": 10.40, "Target": 11.50, "Stop": 10.10},
        {"หุ้น": "GLOBAL", "กลุ่ม": "ก่อสร้าง", "Entry": 16.50, "Target": 18.20, "Stop": 16.10},
        {"หุ้น": "CPALL", "กลุ่ม": "ค้าปลีก", "Entry": 64.50, "Target": 68.00, "Stop": 63.50},
        {"หุ้น": "HMPRO", "กลุ่ม": "ค้าปลีก", "Entry": 6.95, "Target": 7.50, "Stop": 6.80},
    ]
    
    results = []
    for s in stocks_pool:
        # จำลองราคาและการเปลี่ยนแแปลง
        current_price = s["Entry"] * (1 + (random.uniform(-0.01, 0.04)))
        change = ((current_price - s["Entry"]) / s["Entry"]) * 100
        status = "Zing" if change > 2 else "Strong" if change > 0 else "Steady"
        
        results.append({
            "หุ้น": s["หุ้น"],
            "กลุ่ม": s["กลุ่ม"],
            "ราคาล่าสุด": round(current_price, 2),
            "เปลี่ยนแปลง (%)": round(change, 2),
            "Entry": s["Entry"],
            "Target": s["Target"],
            "Stop": s["Stop"],
            "Status": status
        })
    
    # เรียงลำดับตามตัวที่เปลี่ยนแปลงสูงสุด (ซิ่งสุด) และเลือกตามจำนวนที่พี่โบ้ต้องการ
    df = pd.DataFrame(results).sort_values(by="เปลี่ยนแปลง (%)", ascending=False).head(num_items)
    return df

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ")
    num_to_track = st.select_slider(
        "จำนวนหุ้นที่ต้องการติดตาม",
        options=[3, 5, 7, 10, 15],
        value=5,
        help="พี่โบ้เลือกดูเฉพาะตัวท็อปๆ จะได้ตามไหวครับ"
    )
    if st.button("🔄 Refresh Scan", use_container_width=True):
        st.rerun()
    st.divider()
    st.write("🎯 **เป้าหมายวันนี้:** ฿300.00")

# --- Header Area ---
st.title("🎯 SUCHAT PRO SNIPER")
st.caption(f"Dime! Integration • Engineering Edition v2.3 (Tracking Top {num_to_track} Only)")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("เงินในพอร์ต (Dime!)", "฿20,172.03", "172.03 Today")
with col2:
    st.metric("เงินสต็อกสำรอง", "฿40,000.00")
with col3:
    st.metric("ความแม่นยำ AI", "78.5%")
with col4:
    st.metric("LINE Status", "Connected (3165)")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Top Sniper List", "🛡️ พอร์ตแม่ทัพ", "🧮 เครื่องคิดเลข Dime!", "📜 ประวัติกำไร"])

with tab1:
    st.subheader(f"TOP {num_to_track} STRATEGIC WATCHLIST")
    st.info(f"💡 ระบบคัดเฉพาะตัวที่ 'แรง' ที่สุด {num_to_track} อันดับแรกมาให้พี่พิจารณาครับ จะได้ไม่ลายตา")
    
    # Get the data based on selection
    df_display = get_scanned_data(num_to_track)
    
    # Display table with formatting
    st.dataframe(
        df_display, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "ราคาล่าสุด": st.column_config.NumberColumn(format="฿%.2f"),
            "Entry": st.column_config.NumberColumn(format="฿%.2f"),
            "Target": st.column_config.NumberColumn(format="฿%.2f"),
            "Stop": st.column_config.NumberColumn(format="฿%.2f"),
            "เปลี่ยนแปลง (%)": st.column_config.NumberColumn(format="%.2f%%"),
        }
    )

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
        ### วิเคราะห์จากระบบ
        พอร์ตตอนนี้สมดุลดีครับ:
        - **ปันผล:** TISCO / SCB
        - **เงินซิ่ง:** พร้อมล่าส่วนต่าง
        """)
        if st.button("เติมเงินจากสต็อก 40K", use_container_width=True):
            st.success("คำสั่งเติมเงินเรียบร้อย!")

with tab3:
    st.subheader("DIME! CALCULATOR (Net Profit)")
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
    res_col1.metric("กำไรสุทธิ (Net)", f"฿{net_profit:,.2f}")
    res_col2.metric("ค่าธรรมเนียมรวม", f"฿{fees:,.2f}", delta_color="inverse")

with tab4:
    st.subheader("PROFIT HISTORY")
    st.success("**12 ก.พ. 26:** +฿172.03 (GPSC/WHA)")
    st.divider()
    st.write("### ยอดสะสมเดือนนี้")
    st.title("฿172.03")
    st.progress(0.57, text="57% ของเป้าหมาย ฿300")

st.divider()
st.caption("© 2026 SUCHAT ENGINEERING TRADING SYSTEM • EXCLUSIVELY FOR P'BO")
