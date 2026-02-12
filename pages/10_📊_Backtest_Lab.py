import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import json

# --- 1. ตั้งค่า LINE Messaging API (Suchat501) ---
LINE_ACCESS_TOKEN = "H43q8chMtySOrsR4jUo+A7Vrj+MqRIlwxRRjnGP4jnlwnl7CQRRmrtmgbLuTr6ABMPD0tPC8GFIHEdU/AFGLRef7F1ROXUrfhJlgwJwEchvW+V0EJxbV2gkqPrn1EpoRqOBPOQaeFmazkft+d0u8WQdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "Ue09863f4de737b7a9bb131623b06dc22"

def send_to_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

# --- 2. หน้าจอ Streamlit ---
st.set_page_config(page_title="Backtest Lab", page_icon="📊", layout="wide")

st.title("📊 Backtest Lab (Level 5)")
st.write(f"สวัสดีครับพี่โบ้! ระบบพร้อมจำลองแผนการลงทุนย้อนหลังให้พี่แล้ว")

# ส่วนรับค่าอินพุต
col_in1, col_in2 = st.columns(2)
with col_in1:
    symbol = st.text_input("ระบุชื่อหุ้นที่ต้องการทดสอบ (เช่น TISCO, GPSC, WHA)", "TISCO").upper()
with col_in2:
    period = st.selectbox("เลือกช่วงเวลาย้อนหลัง", ["1y", "2y", "5y", "max"], index=0)

if st.button("🚀 เริ่มการทดสอบ (Backtest)"):
    with st.spinner('กำลังคำนวณข้อมูลย้อนหลัง...'):
        ticker_symbol = f"{symbol}.BK"
        data = yf.download(ticker_symbol, period=period)

        if not data.empty:
            # คำนวณค่าทางสถิติ
            start_price = float(data['Close'].iloc[0])
            end_price = float(data['Close'].iloc[-1])
            max_price = float(data['High'].max())
            min_price = float(data['Low'].min())
            total_return = ((end_price - start_price) / start_price) * 100

            # แสดงผล Metrics
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("ราคาเริ่มต้น", f"{start_price:.2f}")
            c2.metric("ราคาปัจจุบัน", f"{end_price:.2f}")
            c3.metric("จุดสูงสุด (High)", f"{max_price:.2f}")
            c4.metric("กำไรสะสม", f"{total_return:.2f}%", delta=f"{total_return:.2f}%")

            # กราฟราคา
            st.subheader(f"📈 กราฟการเติบโตของ {symbol}")
            st.line_chart(data['Close'])

            # บทวิเคราะห์จากระบบ
            st.subheader("📝 บทสรุปจาก Polaris")
            if total_return >= 30:
                result_msg = f"🌟 หุ้น {symbol} ทำกำไรได้ถึง {total_return:.2f}% ซึ่งเกินเป้าหมาย 30% ของพี่โบ้ครับ!"
                st.success(result_msg)
            elif total_return > 0:
                result_msg = f"✅ หุ้น {symbol} ให้ผลตอบแทนเป็นบวก ({total_return:.2f}%) แต่ยังไม่ถึงเป้า 30% ครับ"
                st.info(result_msg)
            else:
                result_msg = f"⚠️ หุ้น {symbol} ผลตอบแทนติดลบ ({total_return:.2f}%) ในช่วงที่เลือกครับ"
                st.warning(result_msg)

            # ส่งสัญญาณเข้า LINE Suchat501
            line_text = f"📊 ผล Backtest หุ้น {symbol}\nช่วงเวลา: {period}\nกำไรสะสม: {total_return:.2f}%\nราคาปัจจุบัน: {end_price:.2f}\nตรวจสอบรายละเอียดในแอปได้เลยครับพี่โบ้!"
            send_to_line(line_text)
            st.write("📲 ส่งผลสรุปเข้า LINE Suchat501 เรียบร้อยแล้ว!")

        else:
            st.error("ไม่พบข้อมูลหุ้นตัวนี้ในตลาดครับพี่")

st.divider()
st.caption("หมายเหตุ: ข้อมูลย้อนหลังเพื่อการตัดสินใจเบื้องต้น ไม่รวมเงินปันผลที่ได้รับ")
