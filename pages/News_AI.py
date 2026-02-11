import streamlit as st
import pandas as pd
import time
import yfinance as yf
import feedparser  # <--- พระเอกคนใหม่ ตัวดูดข่าว
from ai_sentiment import get_ai_sentiment

# ==========================================
# 1. ตั้งค่าหน้า Dashboard & CSS
# ==========================================
st.set_page_config(
    page_title="Polaris AI: Auto Sniper",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .positive-card { border-left: 5px solid #28a745; padding: 15px; background-color: #f0fff4; border-radius: 5px; margin-bottom: 10px; }
    .negative-card { border-left: 5px solid #dc3545; padding: 15px; background-color: #fff5f5; border-radius: 5px; margin-bottom: 10px; }
    .neutral-card { border-left: 5px solid #6c757d; padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 10px; }
    .source-tag { font-size: 0.8em; color: #888; background: #eee; padding: 2px 6px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฟังก์ชันระบบ (ดึงราคา & ดึงข่าว SET)
# ==========================================
def get_stock_price(symbol):
    """ดึงราคาหุ้น Real-time"""
    if not symbol or symbol == "-": return 0.0, 0.0
    try:
        clean_symbol = symbol.strip().upper()
        ticker_symbol = f"{clean_symbol}.BK" if not clean_symbol.endswith(".BK") else clean_symbol
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="2d")
        if len(hist) >= 1:
            last_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) >= 2 else last_price
            change_pct = ((last_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0.0
            return last_price, change_pct
    except:
        pass
    return 0.0, 0.0

def fetch_set_news(limit=3):
    """ดึงข่าวจาก RSS Feed ของตลาดหลักทรัพย์"""
    rss_url = "https://www.set.or.th/rss/news_th.xml"
    feed = feedparser.parse(rss_url)
    news_items = []
    
    # วนลูปเอาข่าวล่าสุดตามจำนวนที่กำหนด (limit)
    for entry in feed.entries[:limit]:
        # พยายามแกะชื่อหุ้นจากหัวข้อข่าว (ส่วนใหญ่จะขึ้นต้นด้วยชื่อหุ้น เช่น "PTT : ...")
        title = entry.title
        symbol = "-"
        if ":" in title:
            possible_symbol = title.split(":")[0].strip()
            # เช็คหน่อยว่าเป็นภาษาอังกฤษล้วนไหม (ชื่อหุ้นต้องเป็น Eng)
            if possible_symbol.isalnum() and possible_symbol.isascii():
                symbol = possible_symbol

        news_items.append({
            "title": title,
            "link": entry.link,
            "published": entry.published,
            "symbol": symbol
        })
    return news_items

# ==========================================
# 3. Sidebar: แผงควบคุม
# ==========================================
st.title("⚡ Polaris AI: Auto Sniper")

with st.sidebar:
    st.header("🎮 Control Center")
    
    # --- Mode 1: Auto Fetch (ของใหม่!) ---
    st.subheader("🤖 โหมดอัตโนมัติ")
    if st.button("🔄 ดึงข่าวล่าสุดจาก SET (3 ข่าว)", type="primary"):
        with st.spinner("⏳ กำลังเชื่อมต่อตลาดหลักทรัพย์..."):
            latest_news = fetch_set_news(limit=3)
            
            # วนลูปวิเคราะห์ทีละข่าว
            for news in latest_news:
                # 1. ให้ AI วิเคราะห์
                ai_result = get_ai_sentiment(news['title'])
                # 2. ให้ Python ดึงราคา (ถ้าแกะชื่อหุ้นได้)
                price, change = get_stock_price(news['symbol'])
                
                # 3. บันทึก
                if 'analysis_history' not in st.session_state:
                    st.session_state.analysis_history = []
                    
                st.session_state.analysis_history.insert(0, {
                    "symbol": news['symbol'],
                    "news": news['title'],
                    "score": ai_result['score'],
                    "reasoning": ai_result['reasoning'],
                    "price": price,
                    "change": change,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "source": "SET Official"
                })
        st.success(f"ดึงข่าวสำเร็จ {len(latest_news)} รายการ!")

    st.divider()

    # --- Mode 2: Manual (แบบเดิม) ---
    with st.form("manual_input"):
        st.subheader("✍️ โหมดกรอกเอง")
        manual_symbol = st.text_input("ชื่อหุ้น", placeholder="เช่น SCB")
        manual_news = st.text_area("เนื้อหาข่าว")
        manual_submit = st.form_submit_button("วิเคราะห์")

# Logic สำหรับโหมด Manual
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []

if manual_submit and manual_news:
    with st.spinner('🤖 Polaris AI กำลังทำงาน...'):
        ai_res = get_ai_sentiment(manual_news)
        mp, mc = get_stock_price(manual_symbol)
        st.session_state.analysis_history.insert(0, {
            "symbol": manual_symbol.upper() if manual_symbol else "-",
            "news": manual_news,
            "score": ai_res['score'],
            "reasoning": ai_res['reasoning'],
            "price": mp,
            "change": mc,
            "timestamp": time.strftime("%H:%M:%S"),
            "source": "Manual Input"
        })

# ==========================================
# 4. แสดงผล (Dashboard)
# ==========================================
# ส่วน Metrics (เหมือนเดิม)
if st.session_state.analysis_history:
    df = pd.DataFrame(st.session_state.analysis_history)
    avg_score = df['score'].mean()
    col1, col2, col3 = st.columns(3)
    col1.metric("จำนวนข่าว", f"{len(df)}", delta="รายการ")
    col2.metric("Sentiment เฉลี่ย", f"{avg_score:.2f}")
    market_mood = "Bullish (กระทิง)" if avg_score > 0 else "Bearish (หมี)" if avg_score < 0 else "Neutral"
    col3.metric("อารมณ์ตลาด", market_mood)
    st.divider()

# ส่วนแสดงรายการข่าว
st.subheader("📰 Live Feed (เรียลไทม์)")
if not st.session_state.analysis_history:
    st.info("👈 กดปุ่ม 'ดึงข่าวล่าสุด' ทางซ้ายมือ เพื่อเริ่มระบบอัตโนมัติ")
else:
    for item in st.session_state.analysis_history:
        # Theme สี
        score = item['score']
        if score > 0:
            theme = ("positive-card", "🟢", "green")
        elif score < 0:
            theme = ("negative-card", "🔴", "red")
        else:
            theme = ("neutral-card", "⚪", "gray")
            
        # Price Tag
        price_tag = ""
        if item['price'] > 0:
            pc_color = "green" if item['change'] >= 0 else "red"
            arrow = "▲" if item['change'] >= 0 else "▼"
            price_tag = f"<span style='background:{pc_color}; color:white; padding:2px 6px; border-radius:4px;'>{item['price']:.2f} ({arrow}{item['change']:.2f}%)</span>"

        st.markdown(f"""
        <div class="{theme[0]}">
            <div style="display:flex; justify-content:space-between;">
                <h4>{theme[1]} Score: {score} {price_tag}</h4>
                <small>{item['timestamp']} | <span class="source-tag">{item.get('source','-')}</span></small>
            </div>
            <p><b>[{item['symbol']}]</b> {item['news']}</p>
            <p style="color:{theme[2]}"><b>💡 AI:</b> {item['reasoning']}</p>
        </div>
        """, unsafe_allow_html=True)
