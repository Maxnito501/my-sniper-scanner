import os
import requests
import yfinance as yf
import pandas as pd
import json

# --- 1. ตั้งค่าเป้าหมาย ---
THAI_STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK",
    "PTTEP.BK"
]

FUND_MAPPING = {
    "SCBSEMI": "SMH",
    "SCBRMNDQ": "QQQ",
    "Gold": "GLD",
    "Silver": "SLV"
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

# --- 5. เริ่มปฏิบัติการ (Logic แยกเกณฑ์) ---
print("🚀 Sniper Bot Started...")
alert_msg = "TEST ALERT"

def check_stock(ticker, name=None, threshold=30):
    df = get_data(ticker)
    if df is not None and 'Close' in df.columns:
        try:
            rsi_series = calculate_rsi(df['Close'])
            current_rsi = float(rsi_series.iloc[-1])
            current_price = float(df['Close'].iloc[-1])
            display_name = name if name else ticker
            
            # เช็คเงื่อนไขตามเกณฑ์ที่ส่งมา (30 หรือ 45)
            if current_rsi <= threshold:
                return f"\n🔥 {display_name}\nPrice: {current_price:.2f}\nRSI: {current_rsi:.1f} (เกณฑ์ {threshold})\n"
        except Exception as e:
            print(f"⚠️ Error {ticker}: {e}")
    return ""

# 5.1 เช็คหุ้นไทย (เกณฑ์โหด 30)
for symbol in THAI_STOCKS:
    alert_msg += check_stock(symbol, threshold=30)

# 5.2 เช็คกองทุน/ทองคำ (เกณฑ์ยืดหยุ่น 45)
for name, ticker in FUND_MAPPING.items():
    alert_msg += check_stock(ticker, name, threshold=45)

# --- 6. ส่งข้อความ ---
if alert_msg:
    full_msg = f"🚨 **SNIPER ALERT** 🚨\nพบจังหวะเข้าทำ!:{alert_msg}"
    print("Found opportunities!")
    send_telegram(full_msg)
    send_line(full_msg)
else:
    # (Optional) ส่งบอกหน่อยว่าทำงานแล้ว แต่ไม่มีของ
    # msg_quiet = "☕ ตลาดเงียบครับ (ไม่มีตัวไหนเข้าเกณฑ์)"
    # send_line(msg_quiet) 
    print("Market is quiet (No RSI match).")

