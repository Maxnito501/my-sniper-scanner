import os
import requests
import yfinance as yf
import pandas as pd

# --- 1. รายชื่อหุ้นและกองทุน (ชุดเดียวกับแอป) ---
TARGETS = {
    # หุ้นไทย
    "CPALL": "CPALL.BK", "PTT": "PTT.BK", "LH": "LH.BK", "GULF": "GULF.BK",
    "SCB": "SCB.BK", "ADVANC": "ADVANC.BK", "AOT": "AOT.BK", "KBANK": "KBANK.BK",
    "BDMS": "BDMS.BK", "PTTEP": "PTTEP.BK",
    # กองทุนโลก
    "Semi-Conductor": "SMH", "Nasdaq-100": "QQQ", 
    "S&P 500": "SPY", "Quality": "QUAL", "Gold": "GLD","Apple (King)": "AAPL","Nvidia (AI God)": "NVDA"
}

# --- 2. ฟังก์ชันส่งข้อความ ---
def send_msg(msg):
    # ส่ง LINE
    line_token = os.environ.get('LINE_ACCESS_TOKEN')
    line_uid = os.environ.get('LINE_USER_ID')
    if line_token and line_uid:
        try:
            requests.post(
                'https://api.line.me/v2/bot/message/push',
                headers={'Authorization': f'Bearer {line_token}', 'Content-Type': 'application/json'},
                json={'to': line_uid, 'messages': [{'type': 'text', 'text': msg}]}
            )
            print("✅ Sent LINE")
        except: pass

    # ส่ง Telegram
    tg_token = os.environ.get('TELEGRAM_TOKEN')
    tg_chat = os.environ.get('TELEGRAM_CHAT_ID')
    if tg_token and tg_chat:
        try:
            requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                          json={"chat_id": tg_chat, "text": msg})
            print("✅ Sent Telegram")
        except: pass

# --- 3. วิเคราะห์กลยุทธ์ (Logic เดียวกับ Polaris) ---
def analyze(name, ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        if len(df) < 200: return None
        
        # คำนวณอินดิเคเตอร์
        current_price = df['Close'].iloc[-1]
        ema200 = df['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        # เงื่อนไขแจ้งเตือน (เอาเฉพาะ "ซื้อ")
        signal = None
        
        # 1. RSI ต่ำมาก (ของถูก ไม่สนเทรนด์)
        if current_rsi <= 30:
            signal = f"🛒 BUY DIP (RSI {current_rsi:.1f})"
            
        # 2. ย่อตัวในขาขึ้น (ของดี ราคาย่อ)
        elif 30 < current_rsi < 45 and current_price > ema200:
            signal = f"➕ BUY PULLBACK (Trend Up, RSI {current_rsi:.1f})"
            
        if signal:
            trend_icon = "🐂" if current_price > ema200 else "🐻"
            return f"\n{signal}\nหุ้น: {name}\nราคา: {current_price:,.2f} {trend_icon}"
            
    except: return None
    return None

# --- 4. เริ่มสแกน ---
print("🚀 Polaris Bot Scanning...")
alert_text = ""

for name, ticker in TARGETS.items():
    res = analyze(name, ticker)
    if res: alert_text += res

if alert_text:
    full_msg = f"🧭 POLARIS ALERT (สัญญาณซื้อ){alert_text}"
    print(full_msg)
    send_msg(full_msg)
else:

    print("Market quiet. No buy signals.")
