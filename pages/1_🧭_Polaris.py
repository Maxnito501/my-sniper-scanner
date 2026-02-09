import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Polaris Strategy V6.1", page_icon="💎", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"]  { font-family: 'Kanit', sans-serif; }
    
    .strategy-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e5e7eb; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .buy-text { color: #166534; font-weight: bold; }
    .sell-text { color: #991b1b; font-weight: bold; }
    .wait-text { color: #854d0e; font-weight: bold; }
    
    .personal-zone { background-color: #eff6ff; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; }
    .price-tag { font-size: 1.1em; font-weight: bold; background: #e5e7eb; padding: 2px 8px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

st.title("💎 Polaris V6.1: Detailed Strategy Advisor")
st.markdown("**หมอประจำพอร์ต: แจกแจงกลยุทธ์ สั้น/ยาว/แก้ดอย แบบเจาะจงราคา**")
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

# --- 4. Strategy Engine ---
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
    
    if rsi <= 35:
        action = "🟢 BUY MORE"
        color = "#90EE90"
    elif rsi >= 75:
        action = "🟠 TRIM PORT"
        color = "#FFD700" 
    elif 35 < rsi < 50 and price > ema200:
        action = "🛒 ACCUMULATE"
        color = "#98FB98"
        
    return price, rsi, trend, strategy, action, color, text_color

# --- 5. Dashboard ---
st.subheader("📊 Strategic Dashboard")

data_list = []
all_tickers = STOCKS + list(FUNDS.keys())
my_bar = st.progress(0)

for i, ticker in enumerate(all_tickers):
    df, pe, div, xd = get_data_from_yahoo(ticker)
    
    if df is not None:
        price, rsi, trend, strat, act, col, txt_col = analyze_data(df, pe, div)
        name_show = ticker.replace(".BK", "")
        
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

    # --- 6. Deep Dive & Detailed Advisor ---
    st.write("---")
    
    col_chart, col_decision = st.columns([1.6, 1])
    
    with col_chart:
        st.subheader("🔍 Technical Chart")
        symbol_list = [d["Symbol"] for d in data_list]
        selected_symbol = st.selectbox("เลือกหุ้นเพื่อวิเคราะห์:", symbol_list)
        target = next((t for n, t in all_tickers if n.replace(".BK", "") == selected_symbol), None)

        if target:
            ticker = target['Ticker']
            df_chart, _, div_yield, xd_date = get_data_from_yahoo(ticker)
            
            if df_chart is not None:
                curr_price = float(df_chart['Close'].iloc[-1])
                # คำนวณแนวรับ/ต้าน (จาก High/Low 60 วันล่าสุด)
                recent_low = df_chart['Low'].tail(60).min()
                recent_high = df_chart['High'].tail(60).max()
                ema_50 = df_chart['EMA50'].iloc[-1]
                
                # หาจุดรับที่ปลอดภัย (Support)
                support_level = max(recent_low, ema_50) if curr_price > ema_50 else recent_low
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.7])
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                                low=df_chart['Low'], close=df_chart['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA200'], name='EMA 200', line=dict(color='blue', width=2)), row=1, col=1)
                
                fig.add_hline(y=support_level, line_dash="dot", line_color="green", annotation_text="Support (จุดรอซื้อ)", row=1, col=1)
                fig.add_hline(y=recent_high, line_dash="dot", line_color="red", annotation_text="Resistance (จุดขาย)", row=1, col=1)
                
                colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in df_chart.iterrows()]
                fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
                fig.update_layout(height=600, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)

    with col_decision:
        st.subheader("👨‍⚕️ Portfolio Doctor (วินิจฉัยละเอียด)")
        
        st.markdown('<div class="personal-zone">', unsafe_allow_html=True)
        st.markdown(f"#### 💼 แผนการเล่น {selected_symbol}")
        
        avg_cost = st.number_input("ต้นทุนเฉลี่ย (บาท)", value=0.0, step=0.1, format="%.2f", key=f"cost_{selected_symbol}")
        qty = st.number_input("จำนวนหุ้นที่มี", value=0, step=100, key=f"qty_{selected_symbol}")
        
        # --- Logic วิเคราะห์แบบเจาะจง ---
        if target:
            rsi_val = df_chart['RSI'].iloc[-1]
            stock_type = STOCK_DNA.get(ticker, "Growth")
            
            # --- กลยุทธ์ 1: สายเล่นสั้น (Sniper) ---
            sniper_action = ""
            if rsi_val <= 45 and curr_price <= support_level * 1.015:
                sniper_action = f"<span class='buy-text'>✅ เข้าซื้อได้เลย!</span> (ราคาชนแนวรับ {support_level:.2f})"
            elif curr_price >= recent_high * 0.985:
                 sniper_action = f"<span class='sell-text'>💰 ขายทำกำไร!</span> (ราคาชนต้าน {recent_high:.2f})"
            else:
                 sniper_action = f"<span class='wait-text'>⏳ รอก่อน</span> (จุดรอซื้อถัดไป: {support_level:.2f})"
            
            st.markdown(f"""
            <div class="strategy-card">
                <b>🔫 สายเล่นสั้น (Sniper):</b><br>
                {sniper_action}
            </div>
            """, unsafe_allow_html=True)

            # --- กลยุทธ์ 2: สายถือยาว (Investor) ---
            investor_action = ""
            if stock_type == "Dividend":
                investor_action = f"🛡️ **หุ้นปันผล:** ถือยาวได้ ไม่ต้องขาย (รอรับปันผล {div_yield:.2f}%)"
            else:
                if curr_price > df_chart['EMA200'].iloc[-1]:
                    investor_action = "💎 **หุ้นเติบโต:** รันเทรนด์ต่อ (ถือไปเรื่อยๆ จนกว่าจะหลุดเส้นฟ้า)"
                else:
                    investor_action = "⚠️ **เฝ้าระวัง:** ราคาหลุดเทรนด์ ชะลอการซื้อเพิ่ม"
            
            st.markdown(f"""
            <div class="strategy-card">
                <b>🐢 สายถือยาว (Investor):</b><br>
                {investor_action}
            </div>
            """, unsafe_allow_html=True)

            # --- กลยุทธ์ 3: แผนแก้ดอย (Recovery) ---
            if qty > 0 and avg_cost > 0:
                market_val = curr_price * qty
                cost_val = avg_cost * qty
                unrealized = market_val - cost_val
                pct = (unrealized / cost_val) * 100
                
                st.write("---")
                if unrealized < 0:
                    st.error(f"📉 พอร์ตติดลบ: {unrealized:,.0f} ฿ ({pct:.2f}%)")
                    
                    # คำแนะนำถัว
                    if curr_price <= support_level * 1.015:
                        st.success(f"💉 **จังหวะถัวมาแล้ว!** ราคาย่อมาที่แนวรับ {support_level:.2f}")
                        
                        # เครื่องคิดเลขถัว (แสดงเฉพาะตอนขาดทุนและน่าถัว)
                        with st.expander("🧮 คำนวณต้นทุนใหม่ (Average Down)", expanded=True):
                            add_shares = st.number_input("จะซื้อถัวกี่หุ้น?", value=100, step=100, key="add_down")
                            if add_shares > 0:
                                new_avg = ((avg_cost * qty) + (curr_price * add_shares)) / (qty + add_shares)
                                diff = avg_cost - new_avg
                                st.info(f"👉 ต้นทุนจะลดเหลือ: **{new_avg:.2f}** (ลดลง {diff:.2f} บาท)")
                    else:
                        st.warning(f"✋ **ใจเย็นๆ:** อย่าเพิ่งถัวกลางอากาศ รอให้ลงมาที่ **{support_level:.2f}** ก่อน")
                else:
                    st.success(f"🎉 พอร์ตกำไร: +{unrealized:,.0f} ฿ (+{pct:.2f}%)")
                    st.caption("ปล่อยกำไรวิ่งไป (Let Profit Run) หรือแบ่งขายถ้าชนแนวต้าน")

            else:
                st.info("💡 กรอกต้นทุนด้านบน เพื่อดูแผนแก้พอร์ต")

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("โหลดข้อมูลไม่ได้ กรุณา Refresh")
