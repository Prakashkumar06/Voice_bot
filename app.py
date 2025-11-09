import os
import tempfile
import base64
import logging
import requests
from flask import Flask, render_template, request, jsonify
from pydub import AudioSegment
from dotenv import load_dotenv
from utils.speech_to_text import transcribe_with_groq, generate_tts_response_groq


load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Please set GROQ_API_KEY as an environment variable before running the app.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice_bot")


prakash_profile = {
    "life story": "Hi, I am Prakash! I grew up in Bihar and recently finished my B.Tech from NIET. During college, I got really interested in Machine Learning and Generative AI, and since then, I have been exploring projects in that space. I enjoy learning new things and finding creative ways to apply AI to solve real-world problems.",
    "superpower": "Honestly, I don't believe I have a superpower, but I do strive to be like Iron Man — dedicated, creative, and persistent. I believe hard work, consistency, and honesty toward my goals are what truly make me strong.",
    "areas to grow": "I want to grow in large-scale AI deployment, system design, and leadership skills. I am also learning to stay calm and focused when dealing with high-pressure or unexpected situations.",
    "misconception": "Some coworkers assume I am introverted, but I actually enjoy collaborating and exchanging ideas. I am always open to learning — not just professionally, but personally as well.",
    "push boundaries": "I push my boundaries by continuously challenging myself with new projects and technologies. I make it a point to step outside my comfort zone, explore new ideas, and keep improving my skills."
}
profile_context = "\n".join([f"{k.capitalize()}: {v}" for k, v in prakash_profile.items()])



@app.route("/")
def index():
    """Main webpage"""
    return render_template("index.html")


@app.route("/process_audio", methods=["POST"])
def process_audio():
    """
    Handles incoming audio recording, converts it, and returns text + TTS.
    Stops old playback when new question is asked.
    """
    try:
        if "audio_data" not in request.files:
            logger.error("No audio data received.")
            return jsonify({"error": "No audio data received"}), 400

        
        audio_file = request.files["audio_data"]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_webm:
            audio_file.save(tmp_webm.name)
            logger.info(f"🎧 Received audio: {tmp_webm.name}")

            
            tmp_wav_path = tmp_webm.name.replace(".webm", ".wav")
            try:
                sound = AudioSegment.from_file(tmp_webm.name, format="webm")
                sound.export(tmp_wav_path, format="wav")
                logger.info("Audio converted from WebM → WAV successfully.")
            except Exception as e:
                logger.error(f"Failed to convert audio: {e}")
                return jsonify({"error": "Audio conversion failed"}), 500

        
        transcript = transcribe_with_groq(tmp_wav_path)
        logger.info(f" Transcription: {transcript}")

        if not transcript or transcript.strip() == "":
            msg = "I didn't catch that. Please try again."
            return jsonify({
                "transcript": "",
                "response": msg,
                "audio_base64": generate_tts_response_groq(msg, speed=1)
            })

    
        response_text = get_ai_response(transcript)
        logger.info(f"Response: {response_text}")

        
        audio_base64 = generate_tts_response_groq(response_text, speed=1)

        return jsonify({
            "transcript": transcript,
            "response": response_text,
            "audio_base64": audio_base64
        })

    except Exception as e:
        logger.exception("Error processing audio")
        return jsonify({"error": str(e)}), 500




def get_ai_response(prompt: str) -> str:
    """
    Generate an AI response using Prakash's personal profile.
    """
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        system_prompt = (
            f"You are acting as Prakash Kumar, a Machine Learning Engineer. "
            f"Here is his background:\n{profile_context}\n"
            f"Always answer as Prakash himself — humble, confident, and natural. "
            f"Keep answers short, clear, and conversational."
        )

        payload = {
            #"model": "llama-3.3-70b-versatile",
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6,
            "max_tokens": 150
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logger.error(f"Groq API Error: {response.text}")
            return "I'm having trouble answering right now."

        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return "Something went wrong while generating my answer."




if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
