import streamlit as st
import pandas as pd
import time
import yfinance as yf
import feedparser
from ai_sentiment import get_ai_sentiment  # อย่าลืมไฟล์ ai_sentiment.py ต้องอยู่ที่เดียวกัน

# ==========================================
# 1. ตั้งค่าหน้า Home
# ==========================================
st.set_page_config(
    page_title="P'Boh Super App",
    page_icon="🚀",
    layout="wide"
)

# CSS แต่งสวย (การ์ดข่าว + ปุ่ม)
st.markdown("""
<style>
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); }
    .positive-card { border-left: 5px solid #28a745; padding: 15px; background-color: #f0fff4; border-radius: 5px; margin-bottom: 10px; }
    .negative-card { border-left: 5px solid #dc3545; padding: 15px; background-color: #fff5f5; border-radius: 5px; margin-bottom: 10px; }
    .neutral-card { border-left: 5px solid #6c757d; padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 10px; }
    
    /* แต่งปุ่มเมนูให้ใหญ่กดง่าย */
    div.stButton > button {
        width: 100%;
        height: 3em;
        font-weight: bold;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฟังก์ชันระบบ (News & Price Engine)
# ==========================================
def get_stock_price(symbol):
    if not symbol or symbol == "-": return 0.0, 0.0
    try:
        clean = symbol.strip().upper()
        ticker = f"{clean}.BK" if not clean.endswith(".BK") else clean
        hist = yf.Ticker(ticker).history(period="2d")
        if len(hist) >= 1:
            last = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2] if len(hist) >= 2 else last
            chg = ((last - prev) / prev) * 100 if prev > 0 else 0.0
            return last, chg
    except: pass
    return 0.0, 0.0

def fetch_set_news(limit=5):
    feed = feedparser.parse("https://www.set.or.th/rss/news_th.xml")
    items = []
    for entry in feed.entries[:limit]:
        title = entry.title
        symbol = "-"
        if ":" in title:
            possible = title.split(":")[0].strip()
            if possible.isalnum() and possible.isascii(): symbol = possible
        items.append({"title": title, "link": entry.link, "symbol": symbol, "time": entry.published})
    return items

# ==========================================
# 3. ส่วนแสดงผลหลัก (Main Interface)
# ==========================================
st.title("🚀 P'Boh Command Center")
st.caption("ศูนย์บัญชาการวิศวกรรมและการลงทุน | สถานะ: Online 🟢")

# สร้าง Tabs เพื่อแยกเมนู กับ ข่าว ไม่ให้ตีกัน
tab_menu, tab_news = st.tabs(["🏠 เมนูหลัก (Main Menu)", "📰 ข่าวล่าหุ้น (AI Sniper)"])

# ---------------------------------------------------------
# TAB 1: เมนูหลัก (ที่พี่บอกว่าหายไป ผมกู้คืนให้ตรงนี้)
# ---------------------------------------------------------
with tab_menu:
    st.subheader("📌 เลือกเครื่องมือใช้งาน")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🤖 **หมวด AI & Data**")
        # ตรงนี้พี่ต้องแก้ชื่อไฟล์ให้ตรงกับที่พี่ตั้งไว้นะครับ
        if st.button("🌟 Polaris (วิเคราะห์หุ้น)"):
            st.switch_page("pages/Polaris.py") 
        if st.button("🧠 Titan (ผู้ช่วย AI)"):
            st.switch_page("pages/Titan.py")

    with col2:
        st.warning("💰 **หมวดการลงทุน**")
        # ลิงก์ไปหน้า Gold Sniper / หุ้นซิ่ง
        if st.button("🔫 Gold Sniper (หุ้นซิ่ง/ทอง)"):
            st.switch_page("pages/Gold_Sniper.py")
        if st.button("📅 DCA Planner"):
            st.switch_page("pages/DCA_Planner.py")

    with col3:
        st.error("⚙️ **หมวดวิศวกรรม**")
        if st.button("💧 Water Report (ชลประทาน)"):
            st.switch_page("pages/Water_Report.py")
        if st.button("🔧 Tools อื่นๆ"):
            st.write("Coming Soon...")

# ---------------------------------------------------------
# TAB 2: ข่าวล่าหุ้น (ระบบ News Sniper เดิม)
# ---------------------------------------------------------
with tab_news:
    st.header("⚡ Live Market Feed")
    
    # ปุ่มกดดึงข่าว
    col_btn, col_status = st.columns([1, 3])
    with col_btn:
        run_scan = st.button("🔄 สแกนข่าวล่าสุด", type="primary")
    
    if 'home_news_history' not in st.session_state:
        st.session_state.home_news_history = []

    if run_scan:
        with st.spinner("⏳ กำลังเชื่อมต่อดาวเทียมตลาดหลักทรัพย์..."):
            news_items = fetch_set_news(limit=3) # ดึง 3 ข่าวล่าสุด
            for news in news_items:
                ai_res = get_ai_sentiment(news['title'])
                price, change = get_stock_price(news['symbol'])
                
                # บันทึก
                st.session_state.home_news_history.insert(0, {
                    "symbol": news['symbol'],
                    "news": news['title'],
                    "score": ai_res['score'],
                    "reasoning": ai_res['reasoning'],
                    "price": price,
                    "change": change,
                    "timestamp": time.strftime("%H:%M:%S")
                })
        st.success("อัปเดตข้อมูลเรียบร้อย!")

    # แสดงรายการข่าว
    if st.session_state.home_news_history:
        for item in st.session_state.home_news_history:
            # Theme
            score = item['score']
            if score > 0: theme = ("positive-card", "🟢", "green")
            elif score < 0: theme = ("negative-card", "🔴", "red")
            else: theme = ("neutral-card", "⚪", "gray")
            
            # Price Tag
            price_info = ""
            if item['price'] > 0:
                arrow = "▲" if item['change'] >= 0 else "▼"
                color = "green" if item['change'] >= 0 else "red"
                price_info = f"<span style='background:{color}; color:white; padding:2px 8px; border-radius:10px;'>{item['price']} ({arrow}{item['change']:.2f}%)</span>"

            st.markdown(f"""
            <div class="{theme[0]}">
                <div style="display:flex; justify-content:space-between;">
                    <h4>{theme[1]} Score: {score} &nbsp; {price_info}</h4>
                    <small>{item['timestamp']}</small>
                </div>
                <b>[{item['symbol']}]</b> {item['news']}
                <hr style="margin:5px 0">
                <p style="color:{theme[2]}"><b>💡 AI:</b> {item['reasoning']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("กดปุ่ม 'สแกนข่าวล่าสุด' เพื่อเริ่มดึงข้อมูล")
