from fastapi import FastAPI, File, UploadFile
from vosk import Model, KaldiRecognizer
import wave
import json

app = FastAPI()

# Load Vosk model (adjust the path to your model folder)
model = Model("vosk-model-small-en-us-0.15")

@app.post("/stt/")
async def speech_to_text(file: UploadFile = File(...)):
    with wave.open(file.file, "rb") as wav_file:
        if wav_file.getnchannels() != 1 or wav_file.getsampwidth() != 2 or wav_file.getframerate() not in [16000, 8000]:
            return {"error": "Audio file must be WAV format, mono channel, 16-bit, and 16000/8000 Hz."}

        recognizer = KaldiRecognizer(model, wav_file.getframerate())
        data = wav_file.readframes(wav_file.getnframes())
        if len(data) > 0:
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                return {"text": result.get("text", "")}
            else:
                return {"text": recognizer.PartialResult()}
