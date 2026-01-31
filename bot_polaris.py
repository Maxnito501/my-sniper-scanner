import os
import requests
import yfinance as yf
import pandas as pd
import json

# --- 1. ตั้งค่าเป้าหมาย (เพิ่ม Silver) ---
THAI_STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK",
    "PTTEP.BK"
]

FUND_MAPPING = {
    "SCBSEMI": "SMH",      # เซมิคอนดักเตอร์
    "SCBRMNDQ": "QQQ",     # Nasdaq
    "SCBRMS&P500": "SPY",  # S&P 500 (เพิ่มให้ครบ)
    "SCBGQUAL": "QUAL",    # Global Quality (เพิ่มให้ครบ)
    "Gold": "GLD",         # ทองคำ
    "Silver": "SLV",       # <--- น้องใหม่! เงิน (Silver)
    "Apple": "AAPL",
    "Nvidia": "NVDA"
}

# --- 2. ฟังก์ชันส่ง Telegram ---
def send_telegram(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          json={"chat_id": chat_id, "text": message})
            print("✅ Sent to Telegram")
        except Exception as e: print(f"❌ Telegram Error: {e}")

# --- 3. ฟังก์ชันส่ง LINE ---
def send_line(message):
    token = os.environ.get('LINE_ACCESS_TOKEN')
    user_id = os.environ.get('LINE_USER_ID')
    
    if not token or not user_id:
        print("⚠️ LINE Keys missing")
        return

    try:
        clean_msg = message.replace('*', '')
        requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            data=json.dumps({'to': user_id, 'messages': [{'type': 'text', 'text': clean_msg}]})
        )
        print("✅ Sent to LINE")
    except Exception as e: print(f"❌ LINE Error: {e}")

# --- 4. ฟังก์ชันคำนวณ ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            try: df.columns = df.columns.get_level_values(0)
            except: pass
        if len(df) == 0: return None
        return df
    except: return None

# --- 5. เริ่มปฏิบัติการ ---
print("🚀 Sniper Bot Started...")
alert_msg = ""

def check_stock(ticker, name=None):
    df = get_data(ticker)
    if df is not None and 'Close' in df.columns:
        try:
            rsi_series = calculate_rsi(df['Close'])
            current_rsi = float(rsi_series.iloc[-1])
            current_price = float(df['Close'].iloc[-1])
            display_name = name if name else ticker
            
            # เกณฑ์: หุ้นไทย <= 30, กองทุน/นอก <= 45
            threshold = 30 if ".BK" in ticker else 45
            
            if current_rsi <= threshold:
                return f"\n🔥 {display_name}\nPrice: {current_price:.2f}\nRSI: {current_rsi:.1f} (ถูก!)\n"
        except Exception as e:
            print(f"⚠️ Error checking {ticker}: {e}")
    return ""

# เช็คหุ้นไทย
for symbol in THAI_STOCKS: alert_msg += check_stock(symbol)
# เช็คกองทุน/หุ้นนอก
for name, ticker in FUND_MAPPING.items(): alert_msg += check_stock(ticker, name)

# --- 6. ส่งข้อความ ---
if alert_msg:
    full_msg = f"🚨 **SNIPER ALERT** 🚨\n{alert_msg}"
    print("Found opportunities!")
    send_telegram(full_msg)
    send_line(full_msg)
else:
    print("Market is quiet.")
