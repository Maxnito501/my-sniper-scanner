import streamlit as st
import pandas as pd
import time
import yfinance as yf
import feedparser
import requests
import sys
import os

# เทคนิค: เพิ่ม Path ให้หาไฟล์ ai_sentiment.py เจอ
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from ai_sentiment import get_ai_sentiment
except ImportError:
    st.error("❌ หาไฟล์ 'ai_sentiment.py' ไม่เจอ! กรุณาตรวจสอบว่าไฟล์นี้อยู่ที่หน้าหลัก (Root Folder)")
    st.stop()

# ==========================================
# 1. ตั้งค่าหน้า News AI
# ==========================================
st.set_page_config(
    page_title="News AI Sniper",
    page_icon="📰",
    layout="wide"
)

st.markdown("""
<style>
    .positive-card { border-left: 5px solid #28a745; padding: 15px; background-color: #f0fff4; border-radius: 5px; margin-bottom: 10px; }
    .negative-card { border-left: 5px solid #dc3545; padding: 15px; background-color: #fff5f5; border-radius: 5px; margin-bottom: 10px; }
    .neutral-card { border-left: 5px solid #6c757d; padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 10px; }
    div.stButton > button { width: 100%; font-weight: bold; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฟังก์ชันระบบ (Engine)
# ==========================================
def get_stock_price(symbol):
    """ดึงราคาหุ้น Real-time"""
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

def fetch_news_stealth(limit=5):
    """ดึงข่าวแบบหลบหลีก (Stealth Mode) + มีแผนสำรอง"""
    
    # แผน A: ตลาดหลักทรัพย์ (SET)
    url_primary = "https://www.set.or.th/rss/news_th.xml"
    
    # แผน B: ข่าวหุ้นจาก Sanook Money (สำรอง)
    url_backup = "https://www.sanook.com/money/rss/news/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    
    items = []
    source_used = "SET Official"
    
    try:
        # ลองแผน A ก่อน
        response = requests.get(url_primary, headers=headers, timeout=10)
        
        # ถ้า Error (เช่น 403 Forbidden) ให้โยน Exception ไปแผน B เลย
        if response.status_code != 200:
            raise Exception(f"SET Blocked: Status {response.status_code}")
            
        feed = feedparser.parse(response.content)
        
        # ถ้าอ่านได้แต่ไม่มีข่าว (RSS ว่างเปล่า)
        if len(feed.entries) == 0:
            raise Exception("SET Empty Feed")

    except Exception as e:
        # แผน A ล่ม -> เริ่มแผน B (Sanook)
        print(f"Plan A Failed ({e}), Switching to Plan B...")
        source_used = "Sanook Money (Backup)"
        try:
            response = requests.get(url_backup, headers=headers, timeout=10)
            feed = feedparser.parse(response.content)
        except Exception as e_backup:
            return [], f"All sources failed: {e_backup}"

    # แปลงข้อมูลให้เป็น Format เดียวกัน
    for entry in feed.entries[:limit]:
        title = entry.title
        symbol = "-"
        
        # Logic แกะชื่อหุ้น (ปรับให้รองรับทั้ง SET และ Backup)
        # SET format: "PTT : แจ้ง..."
        # Backup format: อาจไม่มีชื่อหุ้นนำหน้า
        if ":" in title:
            possible = title.split(":")[0].strip()
            # เช็คว่าเป็นชื่อหุ้นภาษาอังกฤษไหม (ยาว 2-8 ตัวอักษร)
            if possible.isalnum() and possible.isascii() and 2 <= len(possible) <= 8:
                symbol = possible
        
        items.append({
            "title": title, 
            "link": entry.link, 
            "symbol": symbol, 
            "time": entry.published if 'published' in entry else "Just now",
            "source_name": source_used
        })
        
    return items, None

# ==========================================
# 3. ส่วนแสดงผล (User Interface)
# ==========================================
st.title("📰 News AI Sniper")
st.caption("ระบบดึงข่าวอัตโนมัติ (Anti-Block System Enabled 🛡️)")

# --- ส่วนควบคุม (Sidebar) ---
with st.sidebar:
    st.header("🎮 Control Panel")
    
    st.subheader("🤖 โหมดอัตโนมัติ")
    run_scan = st.button("🔄 สแกนข่าวล่าสุด", type="primary")
    
    st.divider()
    
    st.subheader("✍️ โหมดกรอกเอง")
    with st.form("manual_form"):
        man_symbol = st.text_input("ชื่อหุ้น (Symbol)", placeholder="เช่น DELTA")
        man_text = st.text_area("เนื้อหาข่าว", height=100)
        man_submit = st.form_submit_button("วิเคราะห์")

# --- Logic การทำงาน ---
if 'news_ai_history' not in st.session_state:
    st.session_state.news_ai_history = []

# 1. Auto Scan Logic
if run_scan:
    with st.spinner("⏳ กำลังเจาะระบบข่าว (ลองแผน A -> แผน B)..."):
        news_items, error_msg = fetch_news_stealth(limit=5)
        
        if error_msg:
            st.error(f"⚠️ เกิดข้อผิดพลาด: {error_msg}")
        elif not news_items:
            st.warning("⚠️ ไม่พบข่าวใหม่ในขณะนี้")
        else:
            # แจ้งเตือนว่าใช้แหล่งข่าวไหน
            source_name = news_items[0]['source_name']
            if "Backup" in source_name:
                st.warning(f"⚠️ SET เชื่อมต่อไม่ได้ ระบบสลับไปใช้แหล่งข่าวสำรอง: {source_name}")
            else:
                st.success(f"✅ เชื่อมต่อ SET สำเร็จ! ({len(news_items)} ข่าว)")

            for news in news_items:
                ai_res = get_ai_sentiment(news['title'])
                price, change = get_stock_price(news['symbol'])
                
                st.session_state.news_ai_history.insert(0, {
                    "symbol": news['symbol'], "news": news['title'],
                    "score": ai_res['score'], "reasoning": ai_res['reasoning'],
                    "price": price, "change": change, "timestamp": time.strftime("%H:%M:%S"),
                    "source": news['source_name']
                })

# 2. Manual Submit Logic
if man_submit and man_text:
    with st.spinner("🤖 AI กำลังอ่านข่าว..."):
        ai_res = get_ai_sentiment(man_text)
        price, change = get_stock_price(man_symbol)
        
        st.session_state.news_ai_history.insert(0, {
            "symbol": man_symbol.upper() if man_symbol else "-",
            "news": man_text,
            "score": ai_res['score'], "reasoning": ai_res['reasoning'],
            "price": price, "change": change, "timestamp": time.strftime("%H:%M:%S"),
            "source": "Manual Input"
        })
    st.success("✅ วิเคราะห์เสร็จสิ้น")

# --- ส่วนแสดงผลรายการข่าว (Feed) ---
st.divider()
st.subheader("📉 Live Analysis Feed")

if not st.session_state.news_ai_history:
    st.info("👈 กดปุ่มสแกนข่าว หรือกรอกข่าวทางซ้ายมือเพื่อเริ่มใช้งาน")
else:
    for item in st.session_state.news_ai_history:
        score = item['score']
        if score > 0: theme = ("positive-card", "🟢", "green")
        elif score < 0: theme = ("negative-card", "🔴", "red")
        else: theme = ("neutral-card", "⚪", "gray")
        
        price_tag = ""
        if item['price'] > 0:
            arrow = "▲" if item['change'] >= 0 else "▼"
            color = "green" if item['change'] >= 0 else "red"
            price_tag = f"<span style='background:{color}; color:white; padding:3px 8px; border-radius:10px; font-size:0.9em;'>{item['price']} ({arrow}{item['change']:.2f}%)</span>"

        st.markdown(f"""
        <div class="{theme[0]}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4>{theme[1]} Score: {score} &nbsp; {price_tag}</h4>
                <small style="color:#666;">{item['timestamp']} | 📡 {item['source']}</small>
            </div>
            <p style="font-size:1.1em;"><b>[{item['symbol']}]</b> {item['news']}</p>
            <hr style="margin:5px 0; border-top: 1px dashed #ccc;">
            <p style="color:{theme[2]}; font-weight:bold;">💡 AI Insight: {item['reasoning']}</p>
        </div>
        """, unsafe_allow_html=True)
