import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
import logging
from gtts import gTTS
from fastapi.responses import StreamingResponse

# Setup logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Endpoint for health check
@app.get("/health")
def health_check():
    return JSONResponse(content={"status": "ok"})

# Endpoint for webhook
@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    logging.info("Received webhook: %s", payload)
    # Handle Telegram messages
    return JSONResponse(content={"status": "received"})

# Function to get weather data
def get_weather(city: str):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    return response.json()

# Function to process general questions using OpenAI
def ask_openai(question: str):
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": question}]} 
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    return response.json()

# Function for text-to-speech
@app.get("/tts")
async def text_to_speech(text: str):
    tts = gTTS(text)
    tts.save("output.mp3")
    return StreamingResponse(open("output.mp3", "rb"), media_type="audio/mpeg")
