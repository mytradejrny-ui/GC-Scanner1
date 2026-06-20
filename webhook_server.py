"""
GC ICT Scanner — TradingView → Telegram Webhook Server
Run: uvicorn webhook_server:app --host 0.0.0.0 --port 8000
"""

import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from datetime import datetime

app = FastAPI(title="GC ICT Alert Server")

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN")   # set in .env
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") # your chat ID
WEBHOOK_SECRET   = os.environ.get("WEBHOOK_SECRET", "")  # optional security token

EMOJI_MAP = {
    "SELL": "🔴",
    "BUY":  "🟢",
    "OB":   "📦",
    "ALERT":"⚠️",
}


def build_message(raw: str) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    emoji = "📊"
    for key, val in EMOJI_MAP.items():
        if key in raw.upper():
            emoji = val
            break
    return f"{emoji} <b>GC FUTURES ALERT</b>\n\n{raw}\n\n🕐 <i>{now}</i>"


async def send_telegram(text: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       text,
        "parse_mode": "HTML",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=payload)
        return r.status_code == 200


@app.post("/webhook")
async def webhook(request: Request):
    # Optional secret check
    if WEBHOOK_SECRET:
        secret = request.headers.get("X-Webhook-Secret", "")
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
