import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
from datetime import date, datetime as dt
import google.generativeai as genai
import requests
import json
import time
import os

# --- 1. GLOBAL CONFIGURATION ---
st.set_page_config(
    page_title="POLARIS: Grand Unified Hub v7.6",
    page_icon="🎯",
    layout="wide"
)

# Premium Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f8fafc; }
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); border: 1px solid #e2e8f0;
    }
    .zing-card {
        padding: 15px; border-radius: 12px; background-color: white;
        border-left: 6px solid #ef4444; margin-bottom: 10px; border: 1px solid #e2e8f0;
    }
    .signal-buy { background-color: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .signal-wait { background-color: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. NOTIFICATION SYSTEM (suchat3165) ---
LINE_ACCESS_TOKEN = "XgyfEQh3dozGzEKKXVDUfWVBfBw+gX3yV976yTMnMnwPb+f9pHmytApjipzjXqhz/4IFB+qzMBpXx53NXTwaMMEZ+ctG6touSTIV4dXVEoWxoy5arbYVkkd2sxNCR0bX3GDc4A/XqjhnB38caUjyjQdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "Ua666a6ab22c5871d5cf4dc99d0f5045c"

def send_sniper_alert(alert_list):
    """ ส่งการแจ้งเตือนแบบรวบยอดเข้า LINE เพื่อประหยัดโควตา """
    if not alert_list: return False
    
    message = f"\n🚀 POLARIS ZING RADAR\n"
    message += f"------------------\n"
    for a in alert_list:
        message += f"🎯 {a['symbol']}: {a['action']}\n"
        message += f"💵 {a['price']:.2f} | RSI: {a['rsi']:.0f}\n"
    message += f"------------------\n"
    message += f"⏰ {dt.now().strftime('%H:%M')} | ลั่นไกใน Dime!"

    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    payload = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    try:
        requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
        return True
    except:
        return False

# --- 3. BATTLE SET 2: SNIPER ZING HUB (Dynamic Expansion) ---

def set_2_sniper_zing_hub():
    st.header("🚀 ชุดที่ 2: Sniper Zing Hub (Dynamic Expansion)")
    
    # ขยายจักรวาลหุ้นซิ่ง (Universe Expansion)
    zing_universe = [
        "WHA.BK", "TRUE.BK", "CPALL.BK", "DELTA.BK", "GULF.BK", "TASCO.BK", "SIRI.BK", "HANA.BK", "ADVANC.BK",
        "JTS.BK", "CCET.BK", "MGI.BK", "EA.BK", "NEX.BK", "OKJ.BK", "MASTER.BK", "COCOCO.BK", "AU.BK",
        "TIDLOR.BK", "SAWAD.BK", "MTC.BK", "ITC.BK", "AAI.BK", "GPSC.BK", "BGRIM.BK"
    ]
    
    with st.sidebar:
        st.subheader("⚙️ Zing Filter Settings")
        min_vol = st.slider("Min Vol Ratio (ความแรงเจ้าเข้า)", 0.5, 3.0, 1.2)
        show_count = st.slider("จำนวนหุ้นที่จะแสดง", 5, 20, 10)

    t1, t2, t3 = st.tabs(["🔥 Dynamic Zing Scanner", "🧪 Backtest Lab", "📰 News AI Sniper"])
    
    with t1:
        st.subheader(f"เรดาร์จับสัญญาณหุ้นซิ่ง (Top {show_count} Candidates)")
        
        with st.spinner("กำลังค้นหาปลาซิ่งในจักรวาล SET..."):
            # Batch Fetch Data
            data = yf.download(zing_universe, period="5d", interval="1d", progress=False)
            results = []
            alerts_to_send = []

            for t in zing_universe:
                try:
                    close_data = data['Close'][t]
                    vol_data = data['Volume'][t]
                    curr_p = close_data.iloc[-1]
                    prev_p = close_data.iloc[-2]
                    chg = ((curr_p/prev_p)-1)*100
                    v_ratio = vol_data.iloc[-1] / vol_data.mean()
                    
                    # RSI Calculation
                    delta = close_data.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rsi = 100 - (100 / (1 + (gain / loss)))
                    last_rsi = rsi.iloc[-1]

                    # --- 🎯 Dynamic Logic (Pre-emptive Strike) ---
                    action = "Wait"
                    # จังหวะเครื่องติด (เตรียมพุ่ง)
                    if v_ratio > 1.2 and 50 <= last_rsi <= 65:
                        action = "✅ BUY (Breakout Ready)"
                    # จังหวะช้อน Reversal
                    elif v_ratio > 1.8 and last_rsi < 40:
                        action = "🔥 BUY (Strong Rebound)"
                    # จังหวะขาย
                    elif last_rsi > 75:
                        action = "🔴 SELL (Overbought)"

                    # กรองเฉพาะตัวที่มี Momentum หรือเข้าเกณฑ์ที่พี่ตั้งไว้
                    if v_ratio >= min_vol or action != "Wait":
                        results.append({
                            "Stock": t.replace(".BK",""),
                            "Price": round(curr_p, 2),
                            "Chg%": round(chg, 2),
                            "RSI": round(last_rsi, 1),
                            "Vol Ratio": round(v_ratio, 2),
                            "Action": action
                        })
                        if "BUY" in action or "SELL" in action:
                            alerts_to_send.append({"symbol": t.replace(".BK",""), "price": curr_p, "rsi": last_rsi, "action": action})

                except: continue

            if results:
                df_res = pd.DataFrame(results).sort_values("Vol Ratio", ascending=False).head(show_count)
                
                # แสดงผลแบบ Table สวยๆ
                st.dataframe(df_res, use_container_width=True, hide_index=True, 
                             column_config={
                                 "Action": st.column_config.TextColumn("คำแนะนำ Sniper"),
                                 "Vol Ratio": st.column_config.ProgressColumn("แรงส่งเจ้ามือ", min_value=0, max_value=3)
                             })

                # ปุ่มส่ง Alert รวบยอด
                st.divider()
                c_a1, c_a2 = st.columns([2, 1])
                with c_a1:
                    if alerts_to_send:
                        st.warning(f"⚠️ ตรวจพบจังหวะลั่นไก {len(alerts_to_send)} ตัว ในจักรวาลหุ้นซิ่ง!")
                    else:
                        st.info("🐢 ตลาดนิ่ง... ยังไม่มีจังหวะ Sniper ที่ได้เปรียบ")
                with c_a2:
                    if alerts_to_send and st.button("📤 ส่ง Alert เข้า LINE (รวบยอด)", use_container_width=True):
                        send_sniper_alert(alerts_to_send)
                        st.success("ส่งข้อมูลเข้า LINE suchat3165 แล้วครับ!")
            else:
                st.error("ไม่พบข้อมูล หรือตลาดปิดอยู่ครับพี่โบ้")

    with t2:
        st.subheader("🧪 Backtest Lab (View Only)")
        bt_stock = st.text_input("ชื่อหุ้นทดสอบ", "WHA").upper()
        if st.button("🚀 ดูผลงาน 1 ปี"):
            df_bt = yf.download(bt_stock + ".BK", period="1y", progress=False)
            if not df_bt.empty:
                ret = ((df_bt['Close'].iloc[-1]/df_bt['Close'].iloc[0])-1)*100
                st.metric("Total Return", f"{ret:.2f}%")
                st.line_chart(df_bt['Close'])

    with t3:
        st.subheader("📰 News AI Sniper")
        news_input = st.text_area("ก๊อปปี้หัวข้อข่าวมาวางเพื่อประเมินความซิ่ง:")
        if st.button("🔍 วิเคราะห์ข่าว"):
            model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
            res = model.generate_content(f"วิเคราะห์ข่าวหุ้นนี้แบบ Sniper: {news_input} ให้คะแนน -10 ถึง 10 และบอกว่า 'ซิ่งต่อ' หรือ 'พอแค่นี้'")
            st.markdown(f"<div class='positive-card'>{res.text}</div>", unsafe_allow_html=True)

# --- 4. MAIN DISPATCHER ---
def set_1_wealth_intelligence():
    st.header("⚖️ ชุดที่ 1: Wealth Hub")
    st.info("ระบบจัดการ RMF/eDCA พร้อมใช้งาน")

def set_3_gold_sniper():
    st.header("🌕 ชุดที่ 3: Gold Sniper")
    st.info("ระบบ Grid ทองคำพร้อมใช้งาน")

def set_4_wealth_retirement():
    st.header("🛡️ ชุดที่ 4: พอร์ต & Titan")
    st.info("ระบบจัดการความมั่งคั่งระยะยาวพร้อมใช้งาน")

def main():
    with st.sidebar:
        st.title("POLARIS v7.6 🏆")
        st.markdown("<p style='color:gray;'>Dynamic Sniper Manager</p>", unsafe_allow_html=True)
        st.divider()
        mode = st.radio("ชุดปฏิบัติการ", [
            "🚀 ชุดที่ 2: หุ้นซิ่ง Sniper (Expanded)",
            "⚖️ ชุดที่ 1: หุ้นแกร่ง & ภาษี",
            "🌕 ชุดที่ 3: ทองคำ Sniper",
            "🛡️ ชุดที่ 4: พอร์ต & เกษียณ"
        ], index=0)
        st.divider()
        st.caption(f"Engineered by P'Bo 50 | {dt.now().strftime('%H:%M:%S')}")

    if "ชุดที่ 2" in mode: set_2_sniper_zing_hub()
    elif "ชุดที่ 1" in mode: set_1_wealth_intelligence()
    elif "ชุดที่ 3" in mode: set_3_gold_sniper()
    elif "ชุดที่ 4" in mode: set_4_wealth_retirement()

if __name__ == "__main__":
    main()
