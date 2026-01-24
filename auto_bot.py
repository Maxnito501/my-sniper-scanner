import os
import requests
import yfinance as yf
import pandas as pd
import json

# --- 1. ตั้งค่าเป้าหมาย ---
THAI_STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK"
]

FUND_MAPPING = {
    "SCBSEMI": "SMH", "SCBRMNDQ": "QQQ", "Gold": "GLD"
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
    if not token or not user_id: return

    try:
        requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            data=json.dumps({'to': user_id, 'messages': [{'type': 'text', 'text': message.replace('*', '')}]})
        )
        print("✅ Sent to LINE")
    except Exception as e: print(f"❌ LINE Error: {e}")

# --- 4. ฟังก์ชันคำนวณ & ดึงข้อมูล (แก้บั๊ก yfinance ใหม่ตรงนี้) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_data(ticker):
    try:
        # ดึงข้อมูล
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        
        # 🛠️ FIX: แก้ปัญหา yfinance ส่งตารางซ้อน (MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            try:
                # พยายามยุบตารางให้เหลือชั้นเดียว
                df.columns = df.columns.get_level_values(0)
            except:
                pass
                
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
            # คำนวณ RSI
            rsi_series = calculate_rsi(df['Close'])
            
            # 🛠️ FIX: บังคับแปลงเป็นตัวเลขทศนิยม (float) เพื่อแก้ Error Ambiguous
            current_rsi = float(rsi_series.iloc[-1])
            current_price = float(df['Close'].iloc[-1])
            
            display_name = name if name else ticker
            
            # ตั้งค่า RSI <= 30 (เปลี่ยนเลขตรงนี้ได้ถ้าอยากให้เตือนเร็วขึ้น)
            if current_rsi <= 30:
                return f"\n🔥 {display_name}\nPrice: {current_price:.2f}\nRSI: {current_rsi:.1f}\n"
        except Exception as e:
            print(f"⚠️ Error checking {ticker}: {e}")
    return ""

# 5.1 เช็คหุ้นไทย
for symbol in THAI_STOCKS:
    alert_msg += check_stock(symbol)

# 5.2 เช็คกองทุน
for name, ticker in FUND_MAPPING.items():
    alert_msg += check_stock(ticker, name)

# --- 6. ส่งข้อความ ---
if alert_msg:
    full_msg = f"🚨 **SNIPER ALERT** 🚨\n{alert_msg}"
    print("Found opportunities!")
    send_telegram(full_msg)
    send_line(full_msg)
else:
    print("Market is quiet (No RSI <= 30).")


