import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Smart DCA Planner", page_icon="📅", layout="wide")

st.title("📅 Smart DCA Planner: ปฏิทินสไนเปอร์ & จุดขายทำกำไร")
st.markdown("**1. หาวันที่ของถูก (DCA) | 2. หาจุดขายทำกำไร (Take Profit) | 3. จับจังหวะสวน (Oracle)**")
st.write("---")

# --- ข้อมูลสินทรัพย์ (ฉบับครบทีม) ---
ASSETS = {
    # หุ้นไทย (10 ตัวหลัก)
    "🇹🇭 PTT (ปตท.)": "PTT.BK",
    "🇹🇭 CPALL (เซเว่น)": "CPALL.BK",
    "🇹🇭 GULF (กัลฟ์)": "GULF.BK",
    "🇹🇭 ADVANC (AIS)": "ADVANC.BK",
    "🇹🇭 PTTEP (สผ.)": "PTTEP.BK",
    "🇹🇭 SCB (ไทยพาณิชย์)": "SCB.BK",
    "🇹🇭 KBANK (กสิกร)": "KBANK.BK",
    "🇹🇭 AOT (ท่าอากาศยาน)": "AOT.BK",
    "🇹🇭 BDMS (รพ.กรุงเทพ)": "BDMS.BK",
    "🇹🇭 LH (แลนด์ฯ)": "LH.BK",
    
    # กองทุนโลก & สินทรัพย์ทางเลือก
    "🌎 SCBSEMI (ใช้ SMH)": "SMH",
    "🌎 SCBRMNDQ (ใช้ QQQ)": "QQQ",
    "🌎 SCBRMS&P500 (ใช้ SPY)": "SPY",
    "🌎 SCBGQUAL (ใช้ QUAL)": "QUAL",
    "🥇 Gold (ทองคำ)": "GLD",
    "🍎 Apple (AAPL)": "AAPL",
    "🚀 Nvidia (NVDA)": "NVDA"
}

# --- Sidebar ---
st.sidebar.header("⚙️ ตั้งค่าการวิเคราะห์")
selected_asset_name = st.sidebar.selectbox("เลือกสินทรัพย์", list(ASSETS.keys()))
years_back = st.sidebar.slider("สถิติย้อนหลัง (ปี)", 1, 5, 3)

ticker = ASSETS[selected_asset_name]

# --- ฟังก์ชัน 1: วิเคราะห์สถิติย้อนหลัง ---
@st.cache_data(ttl=3600)
def analyze_dca_days(ticker, years):
    try:
        start_date = (datetime.date.today() - datetime.timedelta(days=years*365)).strftime('%Y-%m-%d')
        df = yf.download(ticker, start=start_date, progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df = df[['Close']].copy()
        df['Day'] = df.index.day
        df['Month'] = df.index.month
        df['Year'] = df.index.year
        
        monthly_avg = df.groupby(['Year', 'Month'])['Close'].transform('mean')
        df['Diff_Pct'] = ((df['Close'] - monthly_avg) / monthly_avg) * 100
        
        dca_stats = df.groupby('Day')['Diff_Pct'].mean().reset_index()
        return dca_stats
    except: return None

# --- ฟังก์ชัน 2: ดึงค่าปัจจุบัน ---
def get_current_status(ticker):
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_price = df['Close'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        return current_price, current_rsi
    except: return 0, 0

# --- ฟังก์ชัน 3: Bollinger Bands (Oracle) ---
def calculate_bollinger_bands(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['SMA'] = df['Close'].rolling(window=20).mean()
        df['STD'] = df['Close'].rolling(window=20).std()
        df['Upper'] = df['SMA'] + (df['STD'] * 2)
        df['Lower'] = df['SMA'] - (df['STD'] * 2)
        df['PctB'] = (df['Close'] - df['Lower']) / (df['Upper'] - df['Lower'])
        return df
    except: return None

# --- Main Logic ---

# 1. ดึงข้อมูลพื้นฐาน
dca_stats = analyze_dca_days(ticker, years_back)
cur_price, cur_rsi = get_current_status(ticker)
today_day = datetime.date.today().day

# --- Tab Layout ---
tab1, tab2 = st.tabs(["📅 1. ปฏิทิน DCA (หาฤกษ์ซื้อ)", "🔮 2. The Oracle (จับจังหวะสวน)"])

# ==============================================================================
# TAB 1: DCA PLANNER (สถิติรายวัน)
# ==============================================================================
with tab1:
    if dca_stats is not None and cur_price > 0:
        
        best_days_df = dca_stats.sort_values('Diff_Pct').head(5)
        best_days_list = best_days_df['Day'].tolist()
        is_good_day = today_day in best_days_list
        
        st.subheader(f"🎯 คำแนะนำสำหรับ: {selected_asset_name}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"📅 **วันนี้: วันที่ {today_day}**")
            if is_good_day:
                st.success("✅ สถิติบอก: **วันนี้มักจะของถูก!**")
            else:
                st.warning("⚠️ สถิติบอก: วันนี้ราคามักจะแพง/กลางๆ")
                
        with col2:
            rsi_color = "green" if cur_rsi <= 45 else ("red" if cur_rsi >= 70 else "orange")
            st.markdown(f"📊 **RSI ปัจจุบัน: :{rsi_color}[{cur_rsi:.2f}]**")
            st.caption(f"ราคาล่าสุด: {cur_price:,.2f}")
        
        with col3:
            recommendation = ""
            bg_color = ""
            reason = ""
            
            if is_good_day and cur_rsi <= 45:
                recommendation = "💎 PERFECT MATCH! (หวดเลย)"
                reason = "วันดีตามสถิติ + ราคากำลังย่อ (RSI ต่ำ)"
                bg_color = "#d1fae5"
                
            elif is_good_day and cur_rsi > 45:
                recommendation = "✋ WAIT (กับดัก)"
                reason = "ถึงจะเป็นวันดีตามสถิติ แต่ราคาจริงตอนนี้ยังแพงอยู่"
                bg_color = "#fee2e2"
                
            elif not is_good_day and cur_rsi <= 35:
                recommendation = "🔫 SNIPER SHOT (โอกาสพิเศษ)"
                reason = "ไม่ใช่วันนัดหมาย แต่ราคาถูกมากจนต้องซื้อ!"
                bg_color = "#dbeafe"
                
            else:
                recommendation = "⏳ WAIT / DCA ปกติ"
                reason = "ยังไม่มีจังหวะได้เปรียบพิเศษ"
                bg_color = "#f3f4f6"

            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; border: 1px solid #ccc;">
                <h3 style="margin:0; color: #333;">{recommendation}</h3>
                <small>{reason}</small>
            </div>
            """, unsafe_allow_html=True)

        st.write("---")
        st.subheader(f"📊 ปฏิทินความถูกแพง (Heatmap ย้อนหลัง {years_back} ปี)")
        
        dca_stats['Color'] = dca_stats['Diff_Pct'].apply(lambda x: '#22c55e' if x < 0 else '#ef4444')
        dca_stats['Color'] = dca_stats.apply(lambda x: '#3b82f6' if x['Day'] == today_day else x['Color'], axis=1)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dca_stats['Day'],
            y=dca_stats['Diff_Pct'],
            marker_color=dca_stats['Color'],
            text=dca_stats['Diff_Pct'].apply(lambda x: f"{x:.2f}%"),
            textposition='auto'
        ))
        
        fig.update_layout(
            title="สถิติราคาเฉลี่ยรายวัน (เทียบค่าเฉลี่ยเดือน)",
            xaxis_title="วันที่ (แท่งสีฟ้า = วันนี้)",
            yaxis_title="ความต่างราคา (%)",
            xaxis=dict(tickmode='linear', tick0=1, dtick=1),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        best_str = ", ".join([str(d) for d in best_days_list])
        st.success(f"🏆 **ช่วงวันที่น่าเก็บที่สุด (Top 5):** วันที่ {best_str}")

        # --- ส่วนคำนวณจุดขาย (Take Profit Calculator) ---
        st.write("---")
        st.subheader("🧮 เครื่องคิดเลขขายหมู (Take Profit)")
        
        col_calc1, col_calc2, col_calc3 = st.columns(3)
        with col_calc1:
            # ใช้ราคาล่าสุดเป็นค่าตั้งต้น แต่ให้แก้ได้
            buy_price = st.number_input("ต้นทุนที่ซื้อมา (บาท)", value=float(cur_price) if cur_price > 0 else 0.0, format="%.2f")
        with col_calc2:
            target_pct = st.number_input("ต้องการกำไรกี่ %", value=5.0, step=0.5)
        with col_calc3:
            if buy_price > 0:
                sell_price = buy_price * (1 + target_pct/100)
                profit_amt = sell_price - buy_price
                st.metric("🎯 ตั้งขายที่ราคา", f"{sell_price:,.2f}", f"กำไร {profit_amt:,.2f} บ./หุ้น")

    else:
        st.error("ไม่สามารถดึงข้อมูลได้")

# ==============================================================================
# TAB 2: THE ORACLE (Bollinger Bands)
# ==============================================================================
with tab2:
    st.subheader(f"🔮 The Oracle: จับจังหวะสวนตลาด ({selected_asset_name})")
    
    df_oracle = calculate_bollinger_bands(ticker)
    
    if df_oracle is not None:
        last = df_oracle.iloc[-1]
        last_close = last['Close']
        last_upper = last['Upper']
        last_lower = last['Lower']
        last_pct_b = last['PctB']
        
        col_gauge, col_advice = st.columns([1, 2])
        
        with col_gauge:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = last_pct_b * 100,
                title = {'text': "ความถูก/แพง (Relative Price)"},
                gauge = {
                    'axis': {'range': [-20, 120]},
                    'bar': {'color': "black"},
                    'steps': [
                        {'range': [-20, 0], 'color': "darkgreen"},
                        {'range': [0, 20], 'color': "green"},
                        {'range': [20, 80], 'color': "lightgray"},
                        {'range': [80, 100], 'color': "red"},
                        {'range': [100, 120], 'color': "darkred"}
                    ],
                    'threshold': {'line': {'color': "blue", 'width': 4}, 'thickness': 0.75, 'value': last_pct_b * 100}
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        with col_advice:
            status = ""
            action_text = ""
            bg_color = ""
            
            if last_close < last_lower:
                status = "💎 OVERSOLD (ถูกมากผิดปกติ)"
                action_text = "🟢 **ช้อนซื้อทันที (Strong Buy)!** ราคาต่ำกว่ากรอบล่าง มีโอกาสเด้งกลับสูง"
                bg_color = "#d1fae5"
            elif last_close > last_upper:
                status = "🔥 OVERBOUGHT (แพงเกินไป)"
                action_text = "🔴 **เทขายทำกำไร (Sell)!** หรือห้ามซื้อเพิ่ม ราคาอาจย่อตัว"
                bg_color = "#fee2e2"
            elif last_pct_b < 0.2:
                status = "🛒 CHEAP (ราคาถูก)"
                action_text = "🟢 **ทยอยสะสม (Buy)** ได้เปรียบต้นทุน"
                bg_color = "#ecfccb"
            elif last_pct_b > 0.8:
                status = "⚠️ EXPENSIVE (เริ่มแพง)"
                action_text = "🟠 **ระมัดระวัง (Hold/Wait)** อย่าไล่ราคา"
                bg_color = "#ffedd5"
            else:
                status = "⚖️ FAIR (ราคากลางๆ)"
                action_text = "⚪ **ถือ/รอ (Wait)** ราคาวิ่งในกรอบปกติ"
                bg_color = "#f3f4f6"

            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; border: 1px solid #ccc;">
                <h2 style="margin:0;">{status}</h2>
                <p style="font-size: 1.2em; margin-top: 10px;">{action_text}</p>
                <hr>
                <p><strong>ราคาปัจจุบัน:</strong> {last_close:,.2f}</p>
                <p><strong>กรอบล่าง (แนวรับ):</strong> {last_lower:,.2f}</p>
                <p><strong>กรอบบน (แนวต้าน):</strong> {last_upper:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)

        st.subheader("📉 แผนภาพวิเคราะห์จุดกลับตัว")
        fig_bb = go.Figure()
        fig_bb.add_trace(go.Scatter(
            x=df_oracle.index.tolist() + df_oracle.index.tolist()[::-1],
            y=df_oracle['Upper'].tolist() + df_oracle['Lower'].tolist()[::-1],
            fill='toself', fillcolor='rgba(0,100,80,0.1)', line=dict(color='rgba(255,255,255,0)'), name='Bollinger Band'
        ))
        fig_bb.add_trace(go.Scatter(x=df_oracle.index, y=df_oracle['Close'], name='ราคาหุ้น', line=dict(color='black')))
        fig_bb.add_trace(go.Scatter(x=df_oracle.index, y=df_oracle['Upper'], name='ขอบบน (ขาย)', line=dict(color='red', width=1, dash='dot')))
        fig_bb.add_trace(go.Scatter(x=df_oracle.index, y=df_oracle['Lower'], name='ขอบล่าง (ซื้อ)', line=dict(color='green', width=1, dash='dot')))
        fig_bb.add_trace(go.Scatter(x=df_oracle.index, y=df_oracle['SMA'], name='ค่าเฉลี่ย (กลาง)', line=dict(color='blue', width=1)))
        fig_bb.update_layout(height=500, xaxis_title="วันที่", yaxis_title="ราคา", hovermode="x unified")
        st.plotly_chart(fig_bb, use_container_width=True)
