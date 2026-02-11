import streamlit as st
import pandas as pd
import time
import yfinance as yf
import feedparser
from ai_sentiment import get_ai_sentiment

# ==========================================
# 1. ตั้งค่าหน้า Home
# ==========================================
st.set_page_config(
    page_title="P'Boh Super App",
    page_icon="🚀",
    layout="wide"
)

# CSS แต่งสวย
st.markdown("""
<style>
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); }
    .positive-card { border-left: 5px solid #28a745; padding: 15px; background-color: #f0fff4; border-radius: 5px; margin-bottom: 10px; }
    .negative-card { border-left: 5px solid #dc3545; padding: 15px; background-color: #fff5f5; border-radius: 5px; margin-bottom: 10px; }
    .neutral-card { border-left: 5px solid #6c757d; padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 10px; }
    
    div.stButton > button {
        width: 100%;
        height: 3.5em;
        font-weight: bold;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฟังก์ชันระบบ
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
# 3. ส่วนแสดงผลหลัก
# ==========================================
st.title("🚀 P'Boh Command Center")
st.caption("ศูนย์บัญชาการวิศวกรรมและการลงทุน | สถานะ: Online 🟢")

# สร้าง Tabs
tab_menu, tab_news = st.tabs(["🏠 เมนูหลัก (Main Menu)", "📰 ข่าวล่าหุ้น (AI Sniper)"])

# ---------------------------------------------------------
# TAB 1: เมนูหลัก
# ---------------------------------------------------------
with tab_menu:
    st.subheader("📌 เลือกเครื่องมือใช้งาน")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🤖 **AI & Analytics**")
        if st.button("🧭 Polaris (วิเคราะห์หุ้น)"): st.switch_page("pages/1_🧭_Polaris.py") 
        if st.button("🛡 Titan (ผู้ช่วย AI)"): st.switch_page("pages/2_🛡_Titan.py")
        if st.button("📰 News AI (ระบบดูดข่าว)"): st.switch_page("pages/News_AI.py")

    with col2:
        st.warning("💰 **Investment Strategy**")
        if st.button("🗓 DCA Planner"): st.switch_page("pages/3_🗓_DCA_Planner.py")
        if st.button("📊 My Portfolio"): st.switch_page("pages/4_📊_My_Portfolio.py")
        if st.button("🛰 Gold Sniper"): st.switch_page("pages/5_🛰_Gold_Sniper.py")
        if st.button("🚀 Momentum Sniper"): st.switch_page("pages/7_🚀_Momentum_Sniper.py")

    with col3:
        st.error("⚖️ **Engineering & Tools**")
        if st.button("⚖ Tech vs Quality"): st.switch_page("pages/6_⚖_Tech_vs_Quality.py")
        st.caption("🛠 Coming Soon: Water Management System")

# ---------------------------------------------------------
# TAB 2: ข่าวล่าหุ้น (รวมร่าง Auto + Manual)
# ---------------------------------------------------------
with tab_news:
    st.header("⚡ Live Market Feed")
    
    # ส่วนควบคุมด้านบน (ปุ่ม Auto)
    col_btn, col_status = st.columns([1, 3])
    with col_btn:
        run_scan = st.button("🔄 สแกนข่าวล่าสุด (Auto)", type="primary")

    # ส่วนกรอกมือ (Manual Input) - ใส่ไว้ใน Expander จะได้ไม่รก
    with st.expander("✍️ กรอกข่าวเอง (Manual Input) - คลิกที่นี่"):
        with st.form("manual_news_form"):
            col_man1, col_man2 = st.columns([1, 2])
            with col_man1:
                manual_symbol = st.text_input("ชื่อหุ้น (Symbol)", placeholder="เช่น DELTA")
            with col_man2:
                manual_text = st.text_area("เนื้อหาข่าว", placeholder="วางข่าวที่นี่...", height=100)
            
            manual_submit = st.form_submit_button("🚀 วิเคราะห์ทันที")

    # เตรียม Session State
    if 'home_news_history' not in st.session_state:
        st.session_state.home_news_history = []

    # Logic 1: Auto Scan
    if run_scan:
        with st.spinner("⏳ กำลังเชื่อมต่อดาวเทียมตลาดหลักทรัพย์..."):
            news_items = fetch_set_news(limit=5)
            for news in news_items:
                ai_res = get_ai_sentiment(news['title'])
                price, change = get_stock_price(news['symbol'])
                st.session_state.home_news_history.insert(0, {
                    "symbol": news['symbol'], "news": news['title'],
                    "score": ai_res['score'], "reasoning": ai_res['reasoning'],
                    "price": price, "change": change, "timestamp": time.strftime("%H:%M:%S")
                })
        st.success("อัปเดตข้อมูลเรียบร้อย!")

    # Logic 2: Manual Submit
    if manual_submit and manual_text:
        with st.spinner("🤖 Polaris AI กำลังวิเคราะห์ข้อมูลที่คุณป้อน..."):
            ai_res = get_ai_sentiment(manual_text)
            price, change = get_stock_price(manual_symbol)
            st.session_state.home_news_history.insert(0, {
                "symbol": manual_symbol.upper() if manual_symbol else "-",
                "news": manual_text,
                "score": ai_res['score'], "reasoning": ai_res['reasoning'],
                "price": price, "change": change, "timestamp": time.strftime("%H:%M:%S")
            })
        st.success("วิเคราะห์เสร็จสิ้น!")

    # ส่วนแสดงผล (Display Loop)
    if st.session_state.home_news_history:
        for item in st.session_state.home_news_history:
            score = item['score']
            if score > 0: theme = ("positive-card", "🟢", "green")
            elif score < 0: theme = ("negative-card", "🔴", "red")
            else: theme = ("neutral-card", "⚪", "gray")
            
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
        st.info("กดปุ่ม 'สแกนข่าวล่าสุด' หรือ 'กรอกข่าวเอง' เพื่อเริ่มใช้งาน")
