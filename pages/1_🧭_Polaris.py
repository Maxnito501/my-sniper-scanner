import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V6.4", page_icon="💎", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
    
    .buy-zone { background-color: #dcfce7; padding: 15px; border-radius: 10px; border: 2px solid #16a34a; }
    .sell-zone { background-color: #fee2e2; padding: 15px; border-radius: 10px; border: 2px solid #dc2626; }
    .hold-zone { background-color: #f3f4f6; padding: 15px; border-radius: 10px; border: 2px solid #6b7280; }
    .wait-zone { background-color: #fff7ed; padding: 15px; border-radius: 10px; border: 2px solid #f97316; }
    
    .strategy-badge { display: inline-block; padding: 5px 10px; border-radius: 15px; font-weight: bold; font-size: 0.9em; margin-bottom: 10px;}
    .badge-growth { background-color: #e0f2fe; color: #0369a1; border: 1px solid #0369a1; }
    .badge-div { background-color: #f0fdf4; color: #15803d; border: 1px solid #15803d; }
    
    .price-target { font-size: 1.1em; font-weight: bold; color: #1e3a8a; }
</style>
""", unsafe_allow_html=True)

st.title("💎 Polaris V6.4: Strategic Architect (Strict Mode)")
st.markdown("**หมอประจำพอร์ต: ปรับเกณฑ์ RSI ให้เข้มข้นขึ้น เพื่อความปลอดภัย**")
st.write("---")

# --- 2. ข้อมูลหุ้นและนิสัย (Stock DNA) ---
STOCK_DNA = {
    "PTT.BK": "Dividend", "LH.BK": "Dividend", "TISCO.BK": "Dividend", 
    "SCB.BK": "Dividend", "KBANK.BK": "Dividend", "ADVANC.BK": "Dividend",
    "PTTEP.BK": "Dividend", 
    "CPALL.BK": "Growth", "GULF.BK": "Growth", "AOT.BK": "Growth", 
    "BDMS.BK": "Growth", "CPAXT.BK": "Growth", "CRC.BK": "Growth", "CPN.BK": "Growth",
    "SMH": "Growth", "QQQ": "Growth", "SPY": "Growth", "QUAL": "Growth", 
    "GLD": "Asset", "SLV": "Asset", "AAPL": "Growth", "NVDA": "Growth"
}

STOCKS = [k for k in STOCK_DNA.keys() if ".BK" in k]
FUNDS = {k: k for k in STOCK_DNA.keys() if ".BK" not in k}

# --- 3. ฟังก์ชันดึงข้อมูล ---
@st.cache_data(ttl=3600)
def get_data_from_yahoo(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        if len(df) < 50: return None, 0, 0, "-"

        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['VolMA'] = df['Volume'].rolling(20).mean()

        pe = stock.info.get('trailingPE', 0)
        raw_div = stock.info.get('dividendYield', 0)
        div_yield = (raw_div * 100) if raw_div and raw_div < 1 else (raw_div if raw_div else 0)
        if div_yield > 20: div_yield = 0
        
        xd_ts = stock.info.get('exDividendDate')
        xd_date = datetime.fromtimestamp(xd_ts).strftime('%d/%m/%Y') if xd_ts else "-"

        return df, pe, div_yield, xd_date
    except: return None, 0, 0, "-"

# --- 4. Strategy Engine (ปรับเกณฑ์ RSI ใหม่) ---
def analyze_data(df, pe, div):
    price = df['Close'].iloc[-1]
    ema200 = df['EMA200'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    
    if price > ema200:
        trend = "ขาขึ้น 🐂"
        strategy = "⭐ ถือยาว/สะสม"
    else:
        trend = "ขาลง 🐻"
        strategy = "🛡️ เน้นปันผล/ถัว"
    
    action = "Wait"
    color = "white"
    text_color = "black"
    
    # Logic V6.4: เข้มข้นขึ้น (Strict)
    if rsi <= 30:  # เดิม 35
        action = "🟢 SNIPER BUY"
        color = "#90EE90"
    elif rsi >= 75:
        action = "🟠 TAKE PROFIT"
        color = "#FFD700" 
    elif 30 < rsi <= 45 and price > ema200: # ปรับเพดานลงจาก 50 เป็น 45
        action = "🛒 ACCUMULATE" # ซื้อสะสม (Buy on Dip)
        color = "#98FB98"
        
    return price, rsi, trend, strategy, action, color, text_color

# --- 5. Dashboard ---
st.subheader("📊 Strategic Dashboard")

data_list = []
# สร้างลิสต์แบบ (ชื่อโชว์, รหัสหุ้น)
all_tickers = [(s, s) for s in STOCKS] + [(n, t) for n, t in FUNDS.items()]

my_bar = st.progress(0)

for i, (name, ticker) in enumerate(all_tickers):
    df, pe, div, xd = get_data_from_yahoo(ticker)
    
    if df is not None:
        price, rsi, trend, strat, act, col, txt_col = analyze_data(df, pe, div)
        name_show = name.replace(".BK", "")
        
        data_list.append({
            "Symbol": name_show, "Ticker": ticker, "Price": price, "RSI": rsi,
            "Strategy": strat, "Action": act, "P/E": f"{pe:.1f}" if pe else "-",
            "Div %": f"{div:.2f}%" if div else "-", "XD Date": xd,
            "Trend": trend, "Color": col, "TextColor": txt_col
        })
    my_bar.progress((i + 1) / len(all_tickers))
my_bar.empty()

if data_list:
    res_df = pd.DataFrame(data_list)
    cols = ["Symbol", "Price", "RSI", "Strategy", "Action", "P/E", "Div %", "XD Date"]
    
    def highlight_rows(row):
        bg_color = row.get("Color", "white")
        txt_color = row.get("TextColor", "black")
        return [f'background-color: {bg_color}; color: {txt_color}'] * len(row)

    st.dataframe(
        res_df.style.apply(highlight_rows, axis=1).format({"Price": "{:,.2f}", "RSI": "{:.1f}"}),
        column_order=cols, height=500, use_container_width=True
    )

    # --- 6. Deep Dive & Personal Advisor ---
    st.write("---")
    col_chart, col_doctor = st.columns([1.6, 1])
    
    with col_chart:
        st.subheader("🔍 Technical Chart")
        symbol_list = [d["Symbol"] for d in data_list]
        selected_symbol = st.selectbox("เลือกหุ้นเพื่อวิเคราะห์:", symbol_list)
        
        target_data = next((item for item in data_list if item["Symbol"] == selected_symbol), None)

        if target_data:
            ticker = target_data['Ticker']
            df_chart, _, div_yield, xd_date = get_data_from_yahoo(ticker)
            
            if df_chart is not None:
                current_price_default = float(df_chart['Close'].iloc[-1])
                recent_low = df_chart['Low'].tail(60).min()
                recent_high = df_chart['High'].tail(60).max()
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.7])
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                                low=df_chart['Low'], close=df_chart['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA50'], name='EMA 50', line=dict(color='orange', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA200'], name='EMA 200', line=dict(color='blue', width=2)), row=1, col=1)
                
                fig.add_hline(y=recent_low, line_dash="dot", line_color="green", annotation_text="Support (จุดถัว)", row=1, col=1)
                fig.add_hline(y=recent_high, line_dash="dot", line_color="red", annotation_text="Resistance (ขาย)", row=1, col=1)
                
                colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in df_chart.iterrows()]
                fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
                fig.update_layout(height=600, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)

    with col_doctor:
        st.subheader("👨‍⚕️ Strategic Advisor")
        
        is_dividend_stock = div_yield >= 3.0
        stock_badge = "🛡️ หุ้นปันผล/ออมยาว" if is_dividend_stock else "⚡ หุ้นเติบโต/เล่นรอบ"
        badge_class = "badge-div" if is_dividend_stock else "badge-growth"
        
        st.markdown(f'<span class="strategy-badge {badge_class}">{stock_badge}</span> (P/E: {pe:.1f}, Div: {div_yield:.2f}%)', unsafe_allow_html=True)
        
        # 1. แผนสำหรับคน "ไม่มีของ" (ปรับเกณฑ์ตรงนี้ด้วย)
        st.markdown("#### 🛒 กรณี: ยังไม่มีของ (เข้าใหม่)")
        
        entry_rsi = df_chart['RSI'].iloc[-1]
        
        if entry_rsi <= 45: # ปรับจาก 50 ลงมา 45
             if current_price_default <= recent_low * 1.02:
                 st.markdown(f"""
                 <div class="buy-zone">
                    <b>✅ BUY NOW (ซื้อได้เลย):</b><br>
                    ราคาชนแนวรับ ({recent_low:.2f}) + RSI ต่ำ ({entry_rsi:.0f})<br>
                    <span class="price-target">เป้าซื้อ: {current_price_default:.2f}</span>
                 </div>
                 """, unsafe_allow_html=True)
             else:
                 st.markdown(f"""
                 <div class="wait-zone">
                    <b>⏳ WAIT FOR DIP (รออีกนิด):</b><br>
                    ราคายังลอยอยู่เหนือแนวรับ<br>
                    <span class="price-target">รอรับที่: {recent_low:.2f} บาท</span>
                 </div>
                 """, unsafe_allow_html=True)
        else:
             st.markdown(f"""
             <div class="wait-zone">
                <b>✋ WAIT (อย่าเพิ่งไล่):</b> RSI สูง ({entry_rsi:.0f})<br>
                <span class="price-target">รอรับที่แนวรับ: {recent_low:.2f}</span>
             </div>
             """, unsafe_allow_html=True)

        st.write("---")

        # 2. แผนสำหรับคน "มีของ"
        st.markdown("#### 💼 กรณี: มีของอยู่แล้ว")
        
        with st.expander("📝 กรอกต้นทุนเพื่อรับคำแนะนำ", expanded=True):
            avg_cost = st.number_input("ทุนเฉลี่ย", value=0.0, step=0.1, key=f"c_{selected_symbol}")
            qty = st.number_input("จำนวนหุ้น", value=0, step=100, key=f"q_{selected_symbol}")
            
            if qty > 0 and avg_cost > 0:
                unrealized = (current_price_default - avg_cost) * qty
                pct = (unrealized / (avg_cost * qty)) * 100
                
                if unrealized < 0:
                    st.error(f"📉 ติดดอย {pct:.2f}% ({unrealized:,.0f} ฿)")
                    
                    if is_dividend_stock:
                        if current_price_default <= recent_low * 1.015:
                            st.info(f"💉 **แนะนำ:** ซื้อถัวได้เลย! (ราคาอยู่โซนล่าง)")
                            buy_more = st.number_input("ซื้อเพิ่ม (บาท)", value=5000, step=1000)
                            if buy_more > 0:
                                new_shares = buy_more / current_price_default
                                new_avg = ((avg_cost*qty) + buy_more) / (qty + new_shares)
                                st.write(f"👉 ทุนใหม่จะลดเหลือ: **{new_avg:.2f}**")
                        else:
                            st.warning(f"🧱 **แนะนำ:** ถือรอปันผล (รอให้ลงลึกกว่านี้ค่อยถัว)")
                    else: 
                        if current_price_default < recent_low * 0.95:
                             st.error(f"🚨 **แนะนำ:** หลุดแนวรับ! พิจารณา CUT LOSS")
                        else:
                             st.warning("⏳ **แนะนำ:** นิ่งไว้ (Wait)")

                else:
                    st.success(f"🎉 กำไร {pct:.2f}% ({unrealized:,.0f} ฿)")
                    if is_dividend_stock:
                        st.success("🛡️ **แนะนำ:** ถือยาวกินปันผล (Let Profit Run)")
                    else:
                        if current_price_default >= recent_high * 0.98:
                            st.error(f"💰 **แนะนำ:** ขายทำกำไร! (ชนต้าน {recent_high:.2f})")
                        else:
                            st.info(f"🚀 **แนะนำ:** ถือต่อ (เป้าขาย {recent_high:.2f})")
else:
    st.error("โหลดข้อมูลไม่ได้ กรุณา Refresh")
