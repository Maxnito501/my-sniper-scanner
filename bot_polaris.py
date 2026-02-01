import os
import requests
import yfinance as yf
import pandas as pd
import json

# --- 1. ตั้งค่าเป้าหมาย (Polaris List) ---
TARGETS = {
    # หุ้นไทย
    "CPALL": "CPALL.BK", "PTT": "PTT.BK", "LH": "LH.BK", "GULF": "GULF.BK",
    "SCB": "SCB.BK", "ADVANC": "ADVANC.BK", "AOT": "AOT.BK", "KBANK": "KBANK.BK",
    "BDMS": "BDMS.BK", "PTTEP": "PTTEP.BK",
    # กองทุนโลก
    "Semi-Conductor": "SMH", "Nasdaq-100": "QQQ", 
    "S&P 500": "SPY", "Quality": "QUAL", "Gold": "GLD", "Silver": "SLV"
}

# --- 2. ฟังก์ชันส่งข้อความ ---
def send_telegram(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": message}); print("✅ Telegram Sent")
        except: pass

def send_line(message):
    token = os.environ.get('LINE_ACCESS_TOKEN')
    uid = os.environ.get('LINE_USER_ID')
    if token and uid:
        try:
            requests.post('https://api.line.me/v2/bot/message/push',
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                data=json.dumps({'to': uid, 'messages': [{'type': 'text', 'text': message.replace('*', '')}]})
            )
            print("✅ LINE Sent")
        except: pass

# --- 3. คำนวณเทคนิค (Polaris Logic) ---
def get_data(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # EMA & RSI
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
    except: return None

# --- 4. เริ่มสแกน ---
print("🚀 Polaris Bot Started...")
alert_msg = ""

for name, ticker in TARGETS.items():
    df = get_data(ticker)
    if df is not None:
        price = df['Close'].iloc[-1]
        ema200 = df['EMA200'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        signal = None
        # Logic 1: ซื้อของถูก (Panic Buy)
        if rsi <= 30:
            signal = f"💎 BUY DIP (RSI {rsi:.0f})"
        
        # Logic 2: ย่อตัวในขาขึ้น (Trend Buy)
        elif 30 < rsi <= 45 and price > ema200:
            signal = f"🛒 BUY PULLBACK (Trend Up, RSI {rsi:.0f})"
            
        # Logic 3: 🔴 ขายทำกำไร / ระวังดอย (เพิ่มใหม่!)
        elif rsi >= 75:
            signal = f"🔥 OVERHEATED (RSI {rsi:.0f}) - ระวังแรงขาย!"

        if signal:
            trend_icon = "🐂" if price > ema200 else "🐻"
            # จัดรูปแบบข้อความแจ้งเตือน
            alert_msg += f"\n{signal}\n📌 {name}: {price:,.2f} {trend_icon}\n"

# --- 5. ส่งผลลัพธ์ ---
if alert_msg:
    full_msg = f"🧭 **POLARIS SIGNAL** 🧭\n{alert_msg}"
    print("Found signals!")
    send_telegram(full_msg)
    send_line(full_msg)
else:
    print("Market quiet. No signals.")
