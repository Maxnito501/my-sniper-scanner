import os
import requests
import yfinance as yf
import pandas as pd
import json

# --- 1. ตั้งค่าเป้าหมาย (รายชื่อหุ้น) ---
# หุ้นไทย
THAI_STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK"
]

# กองทุน (Map ชื่อให้เข้าใจง่าย)
FUND_MAPPING = {
    "SCBSEMI": "SMH",      # เซมิคอนดักเตอร์
    "SCBRMNDQ": "QQQ",     # Nasdaq
    "Gold": "GLD"          # ทองคำ
}

# --- 2. ฟังก์ชันส่ง Telegram ---
def send_telegram(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, json=payload)
            print("✅ Sent to Telegram")
        except Exception as e:
            print(f"❌ Telegram Error: {e}")

# --- 3. ฟังก์ชันส่ง LINE (พระเอกของเรา) ---
def send_line(message):
    token = os.environ.get('LINE_ACCESS_TOKEN')
    user_id = os.environ.get('LINE_USER_ID')
    
    if not token or not user_id:
        print("⚠️ LINE Keys missing (Skipping LINE)")
        return

    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    # LINE ชอบข้อความ cleanๆ เอาดอกจันออก
    clean_msg = message.replace('*', '')
    data = {
        'to': user_id,
        'messages': [{'type': 'text', 'text': clean_msg}]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            print("✅ Sent to LINE")
        else:
            print(f"❌ LINE Failed: {response.text}")
    except Exception as e:
        print(f"❌ LINE Error: {e}")

# --- 4. ฟังก์ชันคำนวณ RSI ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) == 0: return None
        return df
    except: return None

# --- 5. เริ่มปฏิบัติการ (Main Process) ---
print("🚀 Sniper Bot Started...")
alert_msg = ""

# 5.1 เช็คหุ้นไทย
for symbol in THAI_STOCKS:
    df = get_data(symbol)
    if df is not None:
        rsi = calculate_rsi(df['Close']).iloc[-1]
        price = df['Close'].iloc[-1]
        
        # *** กฎเหล็ก: แจ้งเมื่อ RSI <= 30 ***
        if rsi <= 30:
            alert_msg += f"\n🔥 {symbol}\nPrice: {price:.2f} บาท\nRSI: {rsi:.1f} (ถูกมาก!)\n"

# 5.2 เช็คกองทุน/ต่างประเทศ
for name, ticker in FUND_MAPPING.items():
    df = get_data(ticker)
    if df is not None:
        rsi = calculate_rsi(df['Close']).iloc[-1]
        price = df['Close'].iloc[-1]
        
        if rsi <= 30:
            alert_msg += f"\n🔥 {name} ({ticker})\nPrice: ${price:.2f}\nRSI: {rsi:.1f}\n"

# --- 6. สรุปผลและส่งข้อความ ---
if alert_msg:
    full_message = f"🚨 **SNIPER ALERT** 🚨\nพบของถูกครับนาย!:{alert_msg}"
    print("Found opportunities! Sending alerts...")
    
    # ส่งทั้ง 2 ทาง
    send_telegram(full_message)
    send_line(full_message)
else:
    print("Market is quiet (No RSI <= 30). Zzz...")
