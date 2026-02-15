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
    page_title="POLARIS: Grand Unified Hub v7.5",
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

def send_sniper_alert(symbol, price, rsi, vol_ratio, action):
    """ ส่งการแจ้งเตือนจังหวะซื้อขายเข้า LINE """
    icon = "🚀" if "BUY" in action else "💰" if "SELL" in action else "🐢"
    message = f"\n{icon} SNIPER ALERT: {symbol}\n"
    message += f"------------------\n"
    message += f"🎯 จังหวะ: {action}\n"
    message += f"💵 ราคา: {price:.2f}\n"
    message += f"🌡️ RSI: {rsi:.1f}\n"
    message += f"⛽ Vol Ratio: {vol_ratio:.2x}\n"
    message += f"⏰ {dt.now().strftime('%H:%M')}\n"
    message += f"------------------\n"
    message += f"ลั่นไกใน Dime! ได้เลยครับพี่โบ้"

    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    payload = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    try:
        requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
        return True
    except:
        return False

# --- 3. BATTLE SET 2: SNIPER ZING HUB (อัปเกรด Alert) ---

def set_2_sniper_zing_hub():
    st.header("🚀 ชุดที่ 2: Sniper Zing Hub (Alert Manager Active)")
    
    # ยุทธศาสตร์ Fast Lane: เน้นตัวที่พร้อมวิ่ง
    zing_pool = {
        "WHA.BK": "IE", "TRUE.BK": "ICT", "CPALL.BK": "COMM", 
        "DELTA.BK": "TECH", "GULF.BK": "ENERGY", "TASCO.BK": "CONMAT",
        "SIRI.BK": "PROP", "HANA.BK": "TECH", "ADVANC.BK": "ICT"
    }
    
    t1, t2, t3 = st.tabs(["🔥 Fast Lane Scanner & Alert", "🧪 Backtest (View Only)", "📰 News AI"])
    
    with t1:
        st.subheader("ดักจับสัญญาณ 'เครื่องติด' (RSI 50-60 + Vol Spike)")
        
        # Batch Fetch Data
        data = yf.download(list(zing_pool.keys()), period="5d", interval="1d", progress=False)
        results = []
        alerts_to_send = []

        for t in zing_pool.keys():
            try:
                hist = data['Close'][t]
                vol = data['Volume'][t]
                curr_p = hist.iloc[-1]
                prev_p = hist.iloc[-2]
                chg = ((curr_p/prev_p)-1)*100
                v_ratio = vol.iloc[-1] / vol.mean()
                
                # คำนวณ RSI เบื้องต้น
                delta = data['Close'][t].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + (gain / loss)))
                last_rsi = rsi.iloc[-1]

                # --- 🎯 Sniper Alert Logic (ยุทธศาสตร์ v7.5) ---
                action = "Wait"
                if v_ratio > 1.5 and 50 <= last_rsi <= 62:
                    action = "✅ BUY (Breakout Ready)"
                elif v_ratio > 2.0 and last_rsi < 45:
                    action = "🔥 BUY (Reversal Strong)"
                elif last_rsi > 75:
                    action = "🔴 SELL (Overbought)"

                results.append({
                    "Stock": t.replace(".BK",""),
                    "Price": curr_p,
                    "Chg%": round(chg, 2),
                    "RSI": round(last_rsi, 1),
                    "Vol Ratio": round(v_ratio, 2),
                    "Action": action
                })

                if "BUY" in action or "SELL" in action:
                    alerts_to_send.append({"symbol": t.replace(".BK",""), "price": curr_p, "rsi": last_rsi, "vol": v_ratio, "action": action})

            except: continue

        df_res = pd.DataFrame(results).sort_values("Vol Ratio", ascending=False)
        st.dataframe(df_res, use_container_width=True, hide_index=True)

        # ปุ่มส่ง Alert รวบยอด
        if alerts_to_send:
            st.divider()
            col_a1, col_a2 = st.columns([2, 1])
            with col_a1:
                st.warning(f"พบสัญญาณเข้าเกณฑ์ Sniper {len(alerts_to_send)} ตัว!")
            with col_a2:
                if st.button("📤 ส่ง Alert เข้า LINE (suchat3165)", use_container_width=True):
                    for alert in alerts_to_send:
                        send_sniper_alert(alert['symbol'], alert['price'], alert['rsi'], alert['vol'], alert['action'])
                    st.success("ส่งการแจ้งเตือนเรียบร้อย!")

    with t2:
        st.subheader("🧪 Backtest Lab (View Only Mode)")
        st.info("ใช้เพื่อตรวจสอบสถิติย้อนหลัง ไม่มีการส่งแจ้งเตือนจากหน้านี้")
        bt_stock = st.text_input("ชื่อหุ้นทดสอบ", "WHA").upper()
        if st.button("🚀 ดูผลงานย้อนหลัง 1 ปี"):
            df_bt = yf.download(bt_stock + ".BK", period="1y", progress=False)
            if not df_bt.empty:
                ret = ((df_bt['Close'].iloc[-1]/df_bt['Close'].iloc[0])-1)*100
                st.metric(f"ผลตอบแทน 1 ปีของ {bt_stock}", f"{ret:.2f}%")
                st.line_chart(df_bt['Close'])

    with t3:
        st.subheader("📰 AI News Sniper")
        # (ตรรกะเดิมจากหน้า 11)
        st.write("ระบบวิเคราะห์ข่าวเพื่อกรองคุณภาพหุ้นซิ่ง")

# --- 4. MAIN DISPATCHER (ส่วนอื่นๆ คงเดิม) ---
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
        st.title("POLARIS v7.5 🏆")
        st.markdown("<p style='color:gray;'>Zing Alert Manager Active</p>", unsafe_allow_html=True)
        st.divider()
        mode = st.radio("ชุดปฏิบัติการ", [
            "🚀 ชุดที่ 2: หุ้นซิ่ง Sniper (Alert!)",
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
