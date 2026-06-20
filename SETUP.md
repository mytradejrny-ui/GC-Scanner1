# GC ICT Scanner — Setup Guide

## Files
- `gc_ict_scanner.pine` — Paste into TradingView Pine Editor
- `webhook_server.py`   — Python server: receives TV alerts → sends to Telegram
- `.env.example`        — Rename to `.env` and fill in your credentials

---

## STEP 1 — Create Your Telegram Bot

1. Open Telegram → search `@BotFather`
2. Send `/newbot` → give it a name (e.g. `GC Scanner Bot`)
3. Copy the **token** it gives you (looks like `123456:ABC-DEF...`)
4. Start a chat with your new bot, send it any message
5. Visit this URL in browser (replace TOKEN):
   `https://api.telegram.org/botTOKEN/getUpdates`
6. Copy the `"id"` value inside `"chat"` — that is your **Chat ID**

---

## STEP 2 — Add Pine Script to TradingView

1. Open TradingView → GC1! chart (Gold Futures)
2. Click **Pine Editor** (bottom) → New → paste `gc_ict_scanner.pine`
3. Click **Add to chart**
4. Recommended timeframe: **15min or 30min**

---

## STEP 3 — Set Up TradingView Alerts

For each signal you want:
1. Right-click chart → **Add Alert**
2. Condition: pick `GC ICT SMC Scanner` → choose alert:
   - `🔴 GC SELL — OB + LH + London/NY`
   - `🟢 GC BUY — OB + HL + London/NY`
   - `📦 New Bearish OB Formed`
3. Notifications: tick **Webhook URL**
4. Enter your server URL: `http://YOUR_SERVER_IP:8000/webhook`
5. Message: leave as `{{alert.message}}` (auto-filled by Pine)
6. Set expiry: **Open-ended**

---

## STEP 4 — Run the Webhook Server

### Option A — Run locally (your PC must be on + port forwarded)
```bash
cd C:\Users\AVISHA\GC-Scanner
pip install -r requirements.txt
copy .env.example .env
# Edit .env with your real token and chat ID
uvicorn webhook_server:app --host 0.0.0.0 --port 8000
```
Then use ngrok to expose it: `ngrok http 8000`
Use the ngrok URL in TradingView alert webhook field.

### Option B — Deploy free to Railway (recommended)
1. Go to railway.app → New Project → Deploy from GitHub
2. Upload this folder or connect your repo
3. Add environment variables from `.env` in Railway dashboard
4. Railway gives you a public URL — use that in TradingView

---

## Signal Logic (What triggers an alert)

| Signal | Conditions Required |
|--------|-------------------|
| SELL   | Price in Bearish OB + Lower High confirmed + EMA bearish (20<50<200) + London or NY session |
| BUY    | Price in Bullish OB + Higher Low confirmed + EMA bullish (20>50>200) + London or NY session |
| OB Alert | Price entering any OB during active session |
| New OB | Displacement candle detected → OB formed |

---

## Session Times (EST)
- **London**: 02:00 – 05:00 EST (07:00–10:00 GMT)
- **New York**: 09:30 – 12:00 EST
