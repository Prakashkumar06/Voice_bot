import requests
import json
import base64
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

def transcribe_with_groq(audio_path):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": open(audio_path, "rb")}
    data = {"model": "whisper-large-v3-turbo"}

    response = requests.post(WHISPER_URL, headers=headers, files=files, data=data)

    if response.status_code != 200:
        print("Groq STT Error:", response.text)
        return "Error transcribing audio"

    transcription = response.json().get("text", "").strip()

    
    if len(transcription) < 3:
        return "No clear speech detected."

    return transcription


def generate_tts_response_groq(text, speed=1.3):
    url = "https://api.groq.com/openai/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "playai-tts",
        "voice": "Calum-PlayAI",  
        "input": text,
        "speed": speed
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print("Groq TTS Error:", response.text)
        return None

    return base64.b64encode(response.content).decode("utf-8")

