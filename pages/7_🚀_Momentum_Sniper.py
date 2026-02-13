import streamlit as st
import pandas as pd
import random
from datetime import datetime

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
    .update-text {
        color: #64748b;
        font-size: 0.8rem;
        font-style: italic;
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

# --- Data Source Logic (Updated with Real Prices from Screenshot) ---
def get_scanned_data(num_items):
    # ปรับราคาอ้างอิงตามตลาดจริง (ข้อมูลวันที่ 13 ก.พ. จากภาพ)
    stocks_pool = [
        {"หุ้น": "ADVANC", "กลุ่ม": "สื่อสาร", "Entry": 388.00, "Target": 400.00, "Stop": 384.00},
        {"หุ้น": "TRUE", "กลุ่ม": "สื่อสาร", "Entry": 12.00, "Target": 12.80, "Stop": 11.80},
        {"หุ้น": "WHA", "กลุ่ม": "นิคมฯ", "Entry": 4.10, "Target": 4.30, "Stop": 4.02},
        {"หุ้น": "AMATA", "กลุ่ม": "นิคมฯ", "Entry": 28.00, "Target": 31.00, "Stop": 27.25},
        {"หุ้น": "ROJNA", "กลุ่ม": "นิคมฯ", "Entry": 7.10, "Target": 7.80, "Stop": 6.95},
        {"หุ้น": "SIRI", "กลุ่ม": "อสังหาฯ", "Entry": 1.80, "Target": 1.95, "Stop": 1.76},
        {"หุ้น": "AP", "กลุ่ม": "อสังหาฯ", "Entry": 10.70, "Target": 11.50, "Stop": 10.40},
        {"หุ้น": "CPALL", "กลุ่ม": "ค้าปลีก", "Entry": 64.50, "Target": 68.00, "Stop": 63.50},
        {"หุ้น": "HMPRO", "กลุ่ม": "ค้าปลีก", "Entry": 6.95, "Target": 7.50, "Stop": 6.80},
        {"หุ้น": "DELTA", "กลุ่ม": "เทค", "Entry": 150.00, "Target": 165.00, "Stop": 145.00},
        {"หุ้น": "GULF", "กลุ่ม": "เทค/พลังงาน", "Entry": 54.00, "Target": 58.00, "Stop": 53.00},
        {"หุ้น": "DOHOME", "กลุ่ม": "ก่อสร้าง", "Entry": 10.40, "Target": 11.50, "Stop": 10.10},
    ]
    
    results = []
    for s in stocks_pool:
        # จำลองการอัปเดตราคาให้ใกล้เคียงค่าปัจจุบัน
        if s["หุ้น"] == "ADVANC":
            current_price = 389.00 # ราคาจากรูป
            change = -0.57 # % จากรูป
        else:
            current_price = s["Entry"] * (1 + (random.uniform(-0.01, 0.02)))
            change = ((current_price - s["Entry"]) / s["Entry"]) * 100
        
        status = "Zing" if change > 1.5 else "Strong" if change > 0 else "Steady"
        
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
    
    df = pd.DataFrame(results).sort_values(by="เปลี่ยนแปลง (%)", ascending=False).head(num_items)
    return df

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ ระบบหลังบ้าน")
    data_mode = st.radio("โหมดข้อมูล", ["Live Simulation (Based on Screenshot)", "Manual Update"])
    num_to_track = st.select_slider("จำนวนหุ้นที่ต้องการสแกน", options=[3, 5, 10, 15], value=5)
    if st.button("🔄 อัปเดตราคาล่าสุด", use_container_width=True):
        st.rerun()
    st.divider()
    st.write("📊 **สถิติตลาด (13 ก.พ. 16:35)**")
    st.write(f"SET Index: 1,430.41 (-0.77%)")
    st.write(f"SET50: 964.35 (-0.76%)")
    st.write(f"⏰ **Last Sync:** {datetime.now().strftime('%H:%M:%S')}")

# --- Header Area ---
st.title("🎯 SUCHAT PRO SNIPER")
st.caption(f"Dime! Integration • v2.4 | อัปเดตฐานราคาตามตลาดล่าสุด")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("เงินสดใน Dime!", "฿20,172.03", "172.03 Today")
with col2:
    st.metric("งบสต็อกสำรอง", "฿40,000.00")
with col3:
    st.metric("SET Index", "1,430.41", "-11.12 (-0.77%)", delta_color="inverse")
with col4:
    st.metric("SET50", "964.35", "-7.42 (-0.76%)", delta_color="inverse")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Scan Results", "🛡️ พอร์ตหุ้น", "🧮 Dime! Calc", "📜 บันทึกกำไร"])

with tab1:
    st.subheader(f"TOP {num_to_track} SNIPER LIST")
    st.markdown(f"<p class='update-text'>อัปเดตฐานราคา ADVANC @ 389.00 (อ้างอิง TradingView {datetime.now().strftime('%d/%m/%Y')})</p>", unsafe_allow_html=True)
    
    df_display = get_scanned_data(num_to_track)
    
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
            "Status": st.column_config.TextColumn()
        }
    )
    st.info("💡 ข้อสังเกต: ตลาดลบหนักแบบนี้ ให้เน้นหุ้นที่ทรงแข็งกว่าตลาด (Relative Strength) เช่น ADVANC ที่ยังยืนได้ครับ")

with tab2:
    st.subheader("พอร์ตแม่ทัพ (Core Stocks)")
    p_col1, p_col2 = st.columns([2, 1])
    
    with p_col1:
        # อัปเดตราคา SCB ในพอร์ตตามตลาดจริง (ถ้ามีข้อมูล)
        port_data = [
            {"หุ้น": "TISCO", "จำนวน": 100, "ทุน": 112.50, "ปัจจุบัน": 112.50, "กำไร/ขาดทุน": "0.00%"},
            {"หุ้น": "SCB", "จำนวน": 25, "ทุน": 135.50, "ปัจจุบัน": 139.50, "กำไร/ขาดทุน": "+2.95%"},
        ]
        st.table(port_data)
    
    with p_col2:
        st.success("✅ พอร์ตฝั่งออมยังแข็งแรง")
        st.write("ทิศทางตลาดขาลงแบบนี้ เงินสดคือกระสุนชั้นดีครับ")
        if st.button("เบิกงบจากสต็อก 40K", use_container_width=True):
            st.balloons()
            st.success("กระสุนพร้อมรบ!")

with tab3:
    st.subheader("DIME! CALCULATOR")
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        symbol = st.text_input("ชื่อหุ้นซิ่ง", "ADVANC")
        shares = st.number_input("จำนวนหุ้น", value=100, step=10)
    with c_col2:
        buy_p = st.number_input("ราคาซื้อ", value=388.00, format="%.2f")
        sell_p = st.number_input("ราคาขาย", value=394.00, format="%.2f")
    
    net_profit, fees = calculate_net_profit(buy_p, sell_p, shares)
    
    st.divider()
    res_col1, res_col2 = st.columns(2)
    res_col1.metric("กำไรสุทธิ (หักค่าคอมฯ แล้ว)", f"฿{net_profit:,.2f}")
    res_col2.metric("ค่าธรรมเนียม Dime! (รวม)", f"฿{fees:,.2f}", delta_color="inverse")

with tab4:
    st.subheader("PROFIT LOG")
    st.success("🗓️ 12 ก.พ. 26: ปิดดีล GPSC/WHA กำไรสุทธิ +฿172.03")
    st.divider()
    st.write("### ยอดกำไรสะสม (เป้าหมายทุนแสน)")
    st.title("฿172.03")
    st.progress(0.0017, text="ก้าวแรกที่สำคัญที่สุด!")

st.divider()
st.caption("ระบบโดยวิศวกร เพื่อวิศวกร • อัปเดตราคาอ้างอิง 13 ก.พ. 26")
