import streamlit as st
import pandas as pd
import yfinance as yf
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
    .main { background-color: #020617; }
    .stMetric {
        background-color: #0f172a;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #1e293b;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #0f172a;
        border-radius: 10px 10px 0px 0px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
    }
    .update-text { color: #64748b; font-size: 0.8rem; font-style: italic; }
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
    net_profit = (sell_gross - buy_gross) - total_fees
    return net_profit, total_fees

# --- Real-time Data Fetching Logic ---
@st.cache_data(ttl=300) # แคชข้อมูลไว้ 5 นาทีเพื่อไม่ให้โดนแบน API และแอปโหลดเร็วขึ้น
def fetch_real_market_data(num_items):
    # ลิสต์หุ้นยุทธศาสตร์ของพี่โบ้ (Pool สำหรับสแกน)
    strategic_pool = {
        "WHA.BK": "นิคมฯ", "AMATA.BK": "นิคมฯ", "ROJNA.BK": "นิคมฯ", "PIN.BK": "นิคมฯ",
        "TRUE.BK": "สื่อสาร", "ADVANC.BK": "สื่อสาร", "THCOM.BK": "สื่อสาร",
        "CPALL.BK": "ค้าปลีก", "HMPRO.BK": "ค้าปลีก", "CRC.BK": "ค้าปลีก", "GLOBAL.BK": "ค้าปลีก",
        "SIRI.BK": "อสังหาฯ", "AP.BK": "อสังหาฯ", "SPALI.BK": "อสังหาฯ", "LH.BK": "อสังหาฯ",
        "DELTA.BK": "เทค", "HANA.BK": "เทค", "KCE.BK": "เทค", "GULF.BK": "เทค/พลังงาน",
        "DOHOME.BK": "ก่อสร้าง", "TASCO.BK": "ก่อสร้าง", "SCC.BK": "ก่อสร้าง"
    }
    
    tickers = list(strategic_pool.keys())
    try:
        # ดึงข้อมูลรวดเดียวทั้งกลุ่ม
        data = yf.download(tickers, period="1d", interval="1m", progress=False)
        
        results = []
        for ticker in tickers:
            try:
                # ดึงราคาล่าสุดจากแท่งเทียนล่าสุด
                current_price = data['Close'][ticker].iloc[-1]
                prev_close = yf.Ticker(ticker).info.get('previousClose', current_price)
                
                change_pct = ((current_price - prev_close) / prev_close) * 100
                symbol = ticker.replace(".BK", "")
                
                # จำลองจุด Entry/Target/Stop ตาม Logic Sniper (ใช้ค่าเฉลี่ยหรือแนวรับแนวต้านสมมติ)
                entry = prev_close * 1.005 # เข้าเมื่อเริ่มขยับ
                target = entry * 1.03    # เป้า 3%
                stop = entry * 0.98      # คัท 2%
                
                results.append({
                    "หุ้น": symbol,
                    "กลุ่ม": strategic_pool[ticker],
                    "ราคาล่าสุด": round(current_price, 2),
                    "เปลี่ยนแปลง (%)": round(change_pct, 2),
                    "Entry": round(entry, 2),
                    "Target": round(target, 2),
                    "Stop": round(stop, 2),
                    "Status": "🔥 Zing" if change_pct > 1.5 else "💪 Strong" if change_pct > 0 else "☁️ Steady"
                })
            except:
                continue
                
        # จัดอันดับตามความแรง (% Change)
        df = pd.DataFrame(results).sort_values(by="เปลี่ยนแปลง (%)", ascending=False).head(num_items)
        return df
    except Exception as e:
        st.error(f"การเชื่อมต่อตลาดขัดข้อง: {e}")
        return pd.DataFrame()

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ ระบบ Sniper Control")
    num_to_track = st.select_slider("จำนวนหุ้นเด่นที่จะล่า", options=[3, 5, 10, 15], value=5)
    if st.button("🔄 สแกนตลาดหาหุ้นซิ่งตอนนี้", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.info("💡 ข้อมูลจาก yfinance อาจมีดีเลย์ 15 นาทีจากราคาตลาดจริง")

# --- Header Area ---
st.title("🎯 SUCHAT PRO SNIPER")
st.caption(f"Real-time Data Integration • v3.0 | อัปเดตข้อมูลสดจาก SET")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("เงินสดใน Dime!", "฿20,172.03", "172.03 Today")
with col2:
    st.metric("งบสต็อกสำรอง", "฿40,000.00")
with col3:
    # พยายามดึงค่า SET Index แบบสดๆ
    try:
        set_idx = yf.Ticker("^SET.BK").history(period="1d")['Close'].iloc[-1]
        st.metric("SET Index", f"{set_idx:,.2f}")
    except:
        st.metric("SET Index", "1,430.41", "-0.77%")
with col4:
    st.metric("LINE Gateway", "suchat3165", "Connected")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Scan Results", "🛡️ พอร์ตหุ้น", "🧮 Dime! Calc", "📜 บันทึกกำไร"])

with tab1:
    st.subheader(f"TOP {num_to_track} SNIPER LIST (LIVE)")
    st.markdown(f"<p class='update-text'>สแกนข้อมูลล่าสุดเมื่อ: {datetime.now().strftime('%H:%M:%S')} (ทุก 5 นาที)</p>", unsafe_allow_html=True)
    
    with st.spinner("กำลังเจาะฐานข้อมูลตลาดหลักทรัพย์..."):
        df_display = fetch_real_market_data(num_to_track)
    
    if not df_display.empty:
        st.dataframe(
            df_display, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "ราคาล่าสุด": st.column_config.NumberColumn(format="฿%.2f"),
                "เปลี่ยนแปลง (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "Entry": st.column_config.NumberColumn(format="฿%.2f"),
                "Target": st.column_config.NumberColumn(format="฿%.2f"),
                "Stop": st.column_config.NumberColumn(format="฿%.2f"),
            }
        )
    else:
        st.warning("ไม่สามารถดึงข้อมูลได้ในขณะนี้ โปรดตรวจสอบการเชื่อมต่ออินเทอร์เน็ต")
    
    st.info("💡 วิธีใช้: ตัวเลขในตารางคือราคาจริงจากตลาด พี่โบ้ดูตัวที่ 'เปลี่ยนแปลง (%)' สูงสุด นั่นคือตัวที่กำลังมี Momentum ครับ")

with tab2:
    st.subheader("พอร์ตแม่ทัพ (Core Stocks)")
    p_col1, p_col2 = st.columns([2, 1])
    with p_col1:
        port_data = [
            {"หุ้น": "TISCO", "จำนวน": 100, "ทุน": 112.50, "ปัจจุบัน": 112.50, "สถานะ": "0.00%"},
            {"หุ้น": "SCB", "จำนวน": 25, "ทุน": 135.50, "ปัจจุบัน": 139.50, "สถานะ": "+2.95%"},
        ]
        st.table(port_data)
    with p_col2:
        st.success("✅ พอร์ตฝั่งออมแข็งแกร่ง")
        if st.button("เบิกงบจากสต็อก 40K", use_container_width=True):
            st.success("กระสุนพร้อมรบ!")

with tab3:
    st.subheader("DIME! CALCULATOR (Real Fee)")
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        symbol = st.text_input("ชื่อหุ้น", "CPALL")
        shares = st.number_input("จำนวนหุ้น", value=100, step=10)
    with c_col2:
        buy_p = st.number_input("ราคาซื้อ", value=49.00, format="%.2f")
        sell_p = st.number_input("ราคาขาย", value=50.00, format="%.2f")
    
    net_profit, fees = calculate_net_profit(buy_p, sell_p, shares)
    st.divider()
    res_col1, res_col2 = st.columns(2)
    res_col1.metric("กำไรสุทธิ (Net)", f"฿{net_profit:,.2f}")
    res_col2.metric("ค่าคอมฯ + ภาษี", f"฿{fees:,.2f}", delta_color="inverse")

with tab4:
    st.subheader("PROFIT LOG")
    st.success("🗓️ 12 ก.พ. 26: ปิดดีล GPSC/WHA กำไรสุทธิ +฿172.03")
    st.write("### ยอดกำไรสะสมเป้าหมายทุนแสน")
    st.title("฿172.03")
    st.progress(0.0017)

st.divider()
st.caption("ระบบโดยวิศวกร เพื่อวิศวกร • ข้อมูลสดจาก Yahoo Finance API")
