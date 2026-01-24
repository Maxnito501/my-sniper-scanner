import os
import requests
import yfinance as yf
import pandas as pd
import json

# --- 1. ช่วงตรวจสอบกุญแจ (Diagnostic Check) ---
print("--- 🕵️‍♂️ DIAGNOSTIC MODE ---")
TG_TOKEN = os.environ.get('TELEGRAM_TOKEN')
LINE_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_USER = os.environ.get('LINE_USER_ID')

if TG_TOKEN: print("✅ Found Telegram Key")
else: print("❌ MISSING Telegram Key")

if LINE_TOKEN: print("✅ Found LINE Token")
else: print("⚠️ MISSING LINE Token (Check .yml file!)")

if LINE_USER: print("✅ Found LINE User ID")
else: print("⚠️ MISSING LINE User ID (Check .yml file!)")
print("----------------------------")

# รายชื่อหุ้นและกองทุน
THAI_STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK"
]
FUND_MAPPING = {
    "SCBSEMI": "SMH", "SCBRMNDQ": "QQQ", "Gold": "GLD"
}

# --- 2. ฟังก์ชันส่งข้อความ ---
def send_telegram(message):
    if TG_TOKEN:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {"chat_id": os.environ.get('TELEGRAM_CHAT_ID'), "text": message}
        try: requests.post(url, json=payload); print("✅ Sent to Telegram")
        except Exception as e: print(f"❌ Telegram Error: {e}")

def send_line(message):
    if not LINE_TOKEN or not LINE_USER:
        print("🚫 Skipping LINE: Token or User ID missing")
        return

    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_TOKEN}'
    }
    data = {
        'to': LINE_USER,
        'messages': [{'type': 'text', 'text': message.replace('*', '')}]
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            print("✅ Sent to LINE (Success!)")
        else:
            print(f"❌ LINE Failed: {response.text}")
    except Exception as e:
        print(f"❌ LINE Error: {e}")

# --- 3. คำนวณ RSI ---
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

# --- 4. เริ่มสแกน (บังคับทดสอบ!) ---
print("🚀 Starting Scan...")
msg = ""

# *** โหมดบังคับส่ง: RSI <= 100 (เพื่อให้ไลน์เด้งแน่นอน) ***
TEST_MODE = True 

for sym in THAI_STOCKS:
    df = get_data(sym)
    if df is not None:
        rsi = calculate_rsi(df['Close']).iloc[-1]
        # ถ้า Test Mode = True ให้ส่งตลอด, ถ้า False ให้ส่งเฉพาะ RSI < 30
        threshold = 100 if TEST_MODE else 30
        
        if rsi <= threshold:
            msg += f"\n🎯 {sym} (RSI {rsi:.1f})"

if msg:
    full_msg = f"TEST ALERT (RSI check){msg}"
    send_telegram(full_msg)
    send_line(full_msg)  # <-- เรียกใช้ฟังก์ชันส่ง LINE
else:
    print("Market is quiet.")
