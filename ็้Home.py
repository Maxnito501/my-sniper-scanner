import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import google.generativeai as genai

# --- 1. การตั้งค่าพื้นฐานและธีม ---
st.set_page_config(
    page_title="POLARIS: Unified Command Center",
    page_icon="🎯",
    layout="wide"
)

# ปรับแต่ง CSS ให้ดูพรีเมียม สไตล์วิศวกรโบ้
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .main-header { font-size: 2.5rem; font-weight: 900; color: #0f172a; margin-bottom: 0.5rem; }
    .stMetric { background-color: white !important; border-radius: 15px !important; border: 1px solid #e2e8f0 !important; padding: 15px !important; }
    .strategy-note { background-color: #f1f5f9; padding: 15px; border-radius: 12px; border-left: 5px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันย่อยแต่ละโซน (Modules) ---

def zone_sniper_hub():
    """ รวมฟังก์ชัน: 1.Fund Sniper, 7.Momentum Sniper, 8.Value Investor, 9.Momentum Radar """
    st.header("🎯 Sniper Hub: Daily Market Action")
    tab1, tab2, tab3 = st.tabs(["🚀 Momentum & Radar", "💰 Value & Dividend", "📈 Fund Sniper"])
    
    with tab1:
        st.subheader("สแกนหุ้นซิ่งและแรงส่ง (หน้า 7 & 9)")
        st.info("ใช้สำหรับกรองหุ้นที่มี Volume Spike และกราฟ Reversal กะทันหัน")
        # ใส่โค้ดวิเคราะห์ Momentum ตรงนี้
        
    with tab2:
        st.subheader("หุ้นปันผลและคุณค่า (หน้า 8)")
        st.write("รายการหุ้นที่กระแสเงินสดดี เหมาะสำหรับถือยาวกินปันผล")
        
    with tab3:
        st.subheader("กองทุนแกร่งสะสม (หน้า 1)")
        st.write("เฝ้าจังหวะเข้าซื้อสะสมกองทุนตัวท็อป")

def zone_strategic_rmf():
    """ รวมฟังก์ชัน: 3.DCA Plan, 6.Tech vs Quality """
    st.header("⚖️ Strategic RMF & Tax eDCA")
    st.info("ยุทธศาสตร์การเข้าซื้อ RMF ตามค่า RSI เพื่อลดภาษีสูงสุด")
    # ใส่โค้ด eDCA Calculator และตารางเปรียบเทียบ SCB vs KKP ตรงนี้
    st.write("คำนวณสัดส่วนการเข้าซื้อจันทร์นี้...")

def zone_wealth_retirement():
    """ รวมฟังก์ชัน: 2.Titan เกษียณ, 4.Portfolio สินทรัพย์ปัจจุบัน """
    st.header("🛡️ Wealth & Titan Retirement")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 สินทรัพย์ปัจจุบัน (หน้า 4)")
        st.write("ตรวจสอบสัดส่วนพอร์ตปัจจุบันและ Rebalance")
    with col2:
        st.subheader("👴 Titan: แผนเกษียณ (หน้า 2)")
        st.write("คำนวณเงินเฟ้อและงบประมาณหลังเกษียณ")

def zone_commodity_gold():
    """ รวมฟังก์ชัน: 5.Gold Sniper """
    st.header("🌕 Gold Sniper Strategy")
    st.write("วิเคราะห์เทรนด์ทองคำโลก สำหรับเล่นยามตลาดหุ้นเงียบ")
    # ใส่โค้ดวิเคราะห์กราฟทองคำตรงนี้

def zone_intelligence_lab():
    """ รวมฟังก์ชัน: 10.Backtest Lab และระบบวิเคราะห์ข่าวใหม่ """
    st.header("🧠 Intelligence & Backtest Lab")
    mode = st.radio("เลือกเครื่องมือ", ["Backtest 1 ปี (หน้า 10)", "AI News Sentiment (วิเคราะห์ข่าว)"], horizontal=True)
    
    if mode == "Backtest 1 ปี (หน้า 10)":
        st.subheader("ระบบทดสอบย้อนหลัง")
        # โค้ด Backtest เดิม
    else:
        st.subheader("AI News Analyzer")
        news_text = st.text_area("ก๊อปปี้ข่าวมาวางเพื่อประเมินผลบวก/ลบ:")
        if st.button("วิเคราะห์ข่าวเดี๋ยวนี้"):
            st.write("AI กำลังประเมินผลกระทบต่อ WHA, CPALL และตลาดรวม...")

# --- 3. ส่วนควบคุมการนำทาง (Sidebar) ---

with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>POLARIS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Unified Command Center v3.0</p>", unsafe_allow_html=True)
    st.divider()
    
    selected_zone = st.radio(
        "โซนการทำงาน:",
        [
            "Sniper Hub (หุ้นไทย)",
            "Strategic RMF (กองทุน/ภาษี)",
            "Wealth & Titan (เกษียณ)",
            "Gold Sniper (ทองคำ)",
            "Intelligence Lab (วิเคราะห์ข่าว)"
        ]
    )
    
    st.divider()
    st.caption(f"Update: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# --- 4. การแสดงผลตามเงื่อนไข (Dispatcher) ---

if selected_zone == "Sniper Hub (หุ้นไทย)":
    zone_sniper_hub()
elif selected_zone == "Strategic RMF (กองทุน/ภาษี)":
    zone_strategic_rmf()
elif selected_zone == "Wealth & Titan (เกษียณ)":
    zone_wealth_retirement()
elif selected_zone == "Gold Sniper (ทองคำ)":
    zone_commodity_gold()
else:
    zone_intelligence_lab()
