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

# --- Session State for Alert Quota ---
if 'alerts_sent_today' not in st.session_state:
    st.session_state.alerts_sent_today = 0
if 'last_alert_time' not in st.session_state:
    st.session_state.last_alert_time = "ยังไม่มีการส่ง"

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
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
    }
    .update-text { color: #94a3b8; font-size: 0.8rem; font-style: italic; }
    .quota-box {
        background-color: #1e293b;
        padding: 10px;
        border-radius: 10px;
        border-left: 5px solid #2563eb;
        margin-bottom: 20px;
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
    net_profit = (sell_gross - buy_gross) - total_fees
    return net_profit, total_fees

# --- Real-time Data Fetching with Alert Logic ---
@st.cache_data(ttl=600)
def fetch_zing_stocks(num_items):
    strategic_pool = {
        "TASCO.BK": "วัสดุก่อสร้าง", "DOHOME.BK": "วัสดุก่อสร้าง", "GLOBAL.BK": "วัสดุก่อสร้าง",
        "WHA.BK": "นิคมฯ", "AMATA.BK": "นิคมฯ", "ROJNA.BK": "นิคมฯ",
        "TRUE.BK": "สื่อสาร", "ADVANC.BK": "สื่อสาร", "THCOM.BK": "สื่อสาร",
        "CPALL.BK": "ค้าปลีก", "CRC.BK": "ค้าปลีก", "HMPRO.BK": "ค้าปลีก",
        "SIRI.BK": "อสังหาฯ", "AP.BK": "อสังหาฯ", "SPALI.BK": "อสังหาฯ",
        "DELTA.BK": "เทค", "HANA.BK": "เทค", "KCE.BK": "เทค", "GULF.BK": "เทค/พลังงาน"
    }
    
    tickers = list(strategic_pool.keys())
    results = []
    
    try:
        data = yf.download(tickers, period="5d", interval="1d", progress=False)
        
        for ticker in tickers:
            try:
                hist = data['Close'][ticker]
                vol_hist = data['Volume'][ticker]
                curr_price = hist.iloc[-1]
                prev_price = hist.iloc[-2]
                curr_vol = vol_hist.iloc[-1]
                avg_vol = vol_hist.mean()
                
                change_pct = ((curr_price - prev_price) / prev_price) * 100
                vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 0
                
                status = "🔥 SUPER ZING" if vol_ratio > 2.0 and change_pct > 1.5 else "🚀 MOMENTUM" if change_pct > 0.5 else "😴 STEADY"
                
                results.append({
                    "หุ้น": ticker.replace(".BK", ""),
                    "กลุ่ม": strategic_pool[ticker],
                    "ราคาล่าสุด": round(curr_price, 2),
                    "เปลี่ยนแปลง (%)": round(change_pct, 2),
                    "Vol Ratio (เท่า)": round(vol_ratio, 2),
                    "Entry": round(curr_price, 2),
                    "Target": round(curr_price * 1.04, 2),
                    "Stop": round(curr_price * 0.97, 2),
                    "สถานะ": status
                })
            except:
                continue
                
        df = pd.DataFrame(results).sort_values(by=["Vol Ratio (เท่า)", "เปลี่ยนแปลง (%)"], ascending=False)
        return df
    except Exception as e:
        st.error(f"ระบบดึงข้อมูลขัดข้อง: {e}")
        return pd.DataFrame()

# --- Alert Logic ---
def process_alerts(df):
    # กรองเฉพาะตัวที่เข้าเกณฑ์เตือน (Super Zing)
    zing_candidates = df[df['สถานะ'] == "🔥 SUPER ZING"]
    
    if not zing_candidates.empty:
        st.warning(f"🔔 ตรวจพบหุ้นเข้าเกณฑ์ {len(zing_candidates)} ตัว!")
        
        # แสดงรายการที่จะเตือน
        alert_msg = " | ".join([f"{row['หุ้น']} ({row['ราคาล่าสุด']})" for idx, row in zing_candidates.iterrows()])
        
        if st.session_state.alerts_sent_today < 15:
            if st.button(f"📤 ส่งเตือนเข้า LINE (โควตาเหลือ {15 - st.session_state.alerts_sent_today} ครั้ง)"):
                # Simulation of sending LINE message
                st.session_state.alerts_sent_today += 1
                st.session_state.last_alert_time = datetime.now().strftime('%H:%M:%S')
                st.success(f"ส่งข้อความรวบยอดสำเร็จ: {alert_msg}")
        else:
            st.error("⚠️ โควตาการส่งเตือนวันนี้เต็มแล้ว (15/15) เพื่อประหยัดโควตารายเดือน")

# --- Header Area ---
st.title("🎯 SUCHAT PRO SNIPER v3.2")
st.caption("Smart Alert System • ดักทุกตัว รวบยอดส่ง ประหยัดโควตา")

# --- Quota Dashboard ---
st.markdown(f"""
<div class="quota-box">
    <p style="margin:0; font-size:0.8rem; color:#94a3b8;">DAILY QUOTA STATUS (suchat3165)</p>
    <p style="margin:0; font-size:1.2rem; font-weight:bold; color:#white;">
        ส่งแล้ว: {st.session_state.alerts_sent_today}/15 ครั้ง | อัปเดตล่าสุด: {st.session_state.last_alert_time}
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("เงินสด Dime!", "฿20,172.03", "172.03 Today")
with col2:
    st.metric("งบสต็อก", "฿40,000.00")
with col3:
    st.metric("SET Index", "1,430.41", "-0.77%", delta_color="inverse")
with col4:
    st.metric("Alert Status", f"{15 - st.session_state.alerts_sent_today} Left", "Daily Quota")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["🔥 Zing Scanner", "🛡️ พอร์ตแม่ทัพ", "🧮 เครื่องคิดเลข", "📜 บันทึกกำไร"])

with tab1:
    s_col1, s_col2 = st.columns([3, 1])
    with s_col1:
        st.subheader("TOP SNIPER WATCHLIST")
    with s_col2:
        if st.button("🔄 RE-SCAN NOW", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("กำลังสแกนหาปลาซิ่ง..."):
        num_picks = st.sidebar.slider("จำนวนหุ้นที่จะแสดง", 3, 15, 5)
        df_zing = fetch_zing_stocks(num_picks)
    
    if not df_zing.empty:
        # ระบบจัดการการแจ้งเตือน
        process_alerts(df_zing)
        
        st.dataframe(
            df_zing, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "ราคาล่าสุด": st.column_config.NumberColumn(format="฿%.2f"),
                "เปลี่ยนแปลง (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "Vol Ratio (เท่า)": st.column_config.NumberColumn(help="เกิน 2.0 คือเจ้าเข้า"),
                "Entry": st.column_config.NumberColumn(format="฿%.2f"),
                "Target": st.column_config.NumberColumn(format="฿%.2f"),
                "Stop": st.column_config.NumberColumn(format="฿%.2f"),
            }
        )
    else:
        st.warning("รอสักครู่ ระบบกำลังเชื่อมต่อตลาด...")

with tab2:
    st.subheader("พอร์ตปัจจุบัน")
    p_col1, p_col2 = st.columns([2, 1])
    with p_col1:
        port_data = [
            {"หุ้น": "TISCO", "จำนวน": 100, "ทุน": 112.50, "ปัจจุบัน": 112.50, "สถานะ": "0.00%"},
            {"หุ้น": "SCB", "จำนวน": 25, "ทุน": 135.50, "ปัจจุบัน": 139.50, "สถานะ": "+2.95%"},
        ]
        st.table(port_data)
    with p_col2:
        st.info("💡 ทุนแสนอยู่ไม่ไกลครับพี่โบ้")
        if st.button("เบิกงบสต็อก 40K"): st.balloons()

with tab3:
    st.subheader("เครื่องคิดเลข Dime!")
    c1, c2 = st.columns(2)
    with c1:
        calc_symbol = st.text_input("หุ้น", "TASCO")
        calc_shares = st.number_input("จำนวนหุ้น", value=1000, step=100)
    with c2:
        buy_p = st.number_input("ราคาซื้อ", value=14.00, format="%.2f")
        sell_p = st.number_input("ราคาขาย", value=14.60, format="%.2f")
    
    net, fees = calculate_net_profit(buy_p, sell_p, calc_shares)
    st.divider()
    res1, res2 = st.columns(2)
    res1.metric("กำไรสุทธิ (Net)", f"฿{net:,.2f}")
    res2.metric("ค่าคอมฯ Dime!", f"฿{fees:,.2f}", delta_color="inverse")

with tab4:
    st.subheader("สรุปกำไรสะสม")
    st.success("🗓️ 12 ก.พ. 26: +฿172.03")
    st.progress(0.0017, text="เส้นทางสู่ทุนแสน")

st.divider()
st.caption("Suchat Engineering Trading System • Alert Quota Manager Active")
