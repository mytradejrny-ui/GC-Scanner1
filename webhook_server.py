"""
GC ICT Scanner — TradingView → Telegram Webhook Server
Run: uvicorn webhook_server:app --host 0.0.0.0 --port 8000
"""

import os
import re
import httpx
from fastapi import FastAPI, Request, HTTPException
from datetime import datetime
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")

TICKER_PATTERNS = [
    re.compile(r"\bon\s+([A-Z][A-Z0-9._:!]{1,15})"),
    re.compile(r"\b([A-Z]{2,6}[0-9]?!?)\s+(?:at|@|on)\b"),
    re.compile(r"\b(GC[0-9]?!?|MGC[0-9]?!?|ES[0-9]?!?|NQ[0-9]?!?|MNQ[0-9]?!?|MNQ[UMHZ]\d{4})\b"),
]

TF_PATTERN = re.compile(r"\bTF[:\s]+(\d+[mhDWMs]?|[DWM])\b", re.IGNORECASE)


def extract_meta(raw: str):
    ticker = ""
    for pat in TICKER_PATTERNS:
        m = pat.search(raw)
        if m:
            ticker = m.group(1)
            break
    tf_match = TF_PATTERN.search(raw)
    tf = tf_match.group(1) if tf_match else ""
    return ticker, tf

app = FastAPI(title="GC ICT Alert Server")

TELEGRAM_TOKEN    = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_IDS = [cid.strip() for cid in os.environ.get("TELEGRAM_CHAT_ID", "").split(",") if cid.strip()]
WEBHOOK_SECRET    = os.environ.get("WEBHOOK_SECRET", "")

EMOJI_MAP = {
    "SELL": "🔴",
    "BUY":  "🟢",
    "OB":   "📦",
    "ALERT":"⚠️",
}


def build_message(raw: str) -> str:
    now = datetime.now(EASTERN).strftime("%a %Y-%m-%d %I:%M %p %Z")
    emoji = "📊"
    for key, val in EMOJI_MAP.items():
        if key in raw.upper():
            emoji = val
            break
    ticker, tf = extract_meta(raw)
    footer_parts = [f"🕐 {now}"]
    if ticker:
        footer_parts.append(f"📈 {ticker}")
    if tf:
        footer_parts.append(f"⏱ {tf}")
    footer = "  |  ".join(footer_parts)
    return f"{emoji} <b>FUTURES ALERT</b>\n\n{raw}\n\n<i>{footer}</i>"


async def send_telegram(text: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_IDS:
        print("ERROR: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    sent_any = False
    async with httpx.AsyncClient(timeout=10) as client:
        for chat_id in TELEGRAM_CHAT_IDS:
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
            try:
                r = await client.post(url, json=payload)
                if r.status_code == 200:
                    sent_any = True
                else:
                    print(f"Telegram error for chat {chat_id}: {r.status_code} {r.text}")
            except Exception as e:
                print(f"Telegram exception for chat {chat_id}: {e}")
    return sent_any


@app.post("/webhook")
async def webhook(request: Request):
    # Optional secret check — accept via header OR query param (TV free plan can't send headers)
    if WEBHOOK_SECRET:
        secret = request.headers.get("X-Webhook-Secret") or request.query_params.get("secret", "")
        if secret != WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret")

    raw = (await request.body()).decode("utf-8").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty body")

    print(f"[{datetime.utcnow()}] Received: {raw}")
    message = build_message(raw)
    ok = await send_telegram(message)

    return {"status": "sent" if ok else "telegram_error", "message": raw}


@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
