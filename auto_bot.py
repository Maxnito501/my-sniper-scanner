import os
import requests
import yfinance as yf
import pandas as pd

# --- ตั้งค่า Config ---
# ดึงรหัสลับจาก GitHub Secrets (เดี๋ยวเราไปตั้งค่ากันในขั้นตอนที่ 3)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# รายชื่อหุ้น/กองทุน (ชุดเดียวกับในแอป)
THAI_STOCKS = [
    "CPALL.BK", "PTT.BK", "LH.BK", "GULF.BK", 
    "SCB.BK", "ADVANC.BK", "AOT.BK", "KBANK.BK", "BDMS.BK"
]

FUND_MAPPING = {
    "SCBSEMI (Semiconductor)":   {"ticker": "SMH", "market": "US"},
    "SCBRMNDQ (NASDAQ 100)":     {"ticker": "QQQ", "market": "US"},
    "SCBRMS&P500 (S&P 500)":     {"ticker": "SPY", "market": "US"},
    "SCBGQUAL (Global Quality)": {"ticker": "QUAL", "market": "US"},
    "KKP GB THAI ESG (Thai ESG)":{"ticker": "^SET", "market": "TH"},
    "TISCO (High Dividend)":     {"ticker": "TISCO.BK", "market": "TH"},
    "Gold (ทองคำโลก)":           {"ticker": "GLD", "market": "US"}
}

def send_telegram(message):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
    else:
        print("Error: ไม่พบ Token หรือ Chat ID")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if len(df) == 0: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except: return None

# --- Main Logic ---
print("Running Auto Sniper...")
msg_stocks = ""
for sym in THAI_STOCKS:
    df = get_data(sym)
    if df is not None:
        rsi = calculate_rsi(df['Close']).iloc[-1]
        if rsi <= 30: 
            msg_stocks += f"\n🎯 *{sym.replace('.BK','')}* (RSI {rsi:.1f}) ✅"

msg_funds = ""
for name, info in FUND_MAPPING.items():
    df = get_data(info['ticker'])
    if df is not None:
        rsi = calculate_rsi(df['Close']).iloc[-1]
        if rsi <= 45: 
            msg_funds += f"\n🛒 *{name}* (RSI {rsi:.1f})"

full_msg = ""
if msg_stocks: full_msg += f"\n\n🇹🇭 *หุ้นไทย (Buy):*{msg_stocks}"
if msg_funds: full_msg += f"\n\n🌎 *กองทุน (Accumulate):*{msg_funds}"

# ส่งข้อความเฉพาะเมื่อเจอของถูก (จะได้ไม่รบกวนบ่อย)
if full_msg != "":
    send_telegram(f"⏰ *Auto Alert (4 Times)*{full_msg}")
    print("Sent Alert!")
else:
    print("Market is quiet. No alert sent.")