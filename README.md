# AI-Powered Telegram Assistant

A Telegram bot backed by FastAPI that answers weather queries (OpenWeather) and general questions (OpenAI).  
Supports optional voice responses via gTTS and simple per-user state persistence with SQLite.

---

## Features

- **Weather queries** – `weather today Brussels`, `weather tomorrow Berlin`, `weather 3 days Paris`
- **AI answers** – any non-weather question is forwarded to OpenAI `gpt-4o-mini`
- **Voice mode** – `voice on` / `voice off` toggles voice responses (Telegram voice messages)
- **State persistence** – SQLite stores voice preference and last location per user
- **Health check** – `GET /health`

---

## Local Setup

### 1. Clone & install dependencies

```bash
git clone https://github.com/Xander-Vanlaer/telegram.git
cd telegram
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

Required variables:

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/botfather) |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENWEATHER_API_KEY` | OpenWeather API key |
| `WEBHOOK_BASE_URL` | Public HTTPS URL (e.g. ngrok) |
| `SQLITE_DB_PATH` | Path to SQLite DB (default `data/state.db`) |
| `DEFAULT_LANG` | TTS language code (default `en`) |

### 3. Run locally

```bash
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

### 4. Expose with ngrok (for webhook)

```bash
ngrok http 8080
# Copy the https URL and set WEBHOOK_BASE_URL in .env
```

### 5. Register the Telegram webhook

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://<YOUR_NGROK_URL>/webhook/telegram"}'
```

---

## Docker

### Build

```bash
docker build -t telegram-bot .
```

### Run

```bash
docker run -p 8080:8080 --env-file .env telegram-bot
```

---

## Google Cloud Run Deployment

```bash
gcloud run deploy telegram-bot \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars TELEGRAM_BOT_TOKEN=...,OPENAI_API_KEY=...,OPENWEATHER_API_KEY=...
```

After deployment, register the Cloud Run URL as the Telegram webhook.

---

## Example Interactions

| User message | Bot response |
|---|---|
| `weather today Brussels` | `Current weather in Brussels: 15°C, light rain. Humidity: 72%, Wind: 3.5 m/s.` |
| `weather tomorrow Berlin` | `Tomorrow in Berlin: 12°C, overcast clouds.` |
| `explain photosynthesis` | AI-generated explanation |
| `voice on` | `Voice mode enabled.` + future responses as voice messages |
| `voice off` | `Voice mode disabled.` |
