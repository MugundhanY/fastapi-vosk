from fastapi import FastAPI, File, UploadFile, HTTPException
from vosk import Model, KaldiRecognizer
import wave
import json

app = FastAPI()

# Load the Vosk model (make sure the path to your model is correct)
model = Model("path_to_vosk_model")

@app.post("/stt/")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # Check if the file is a WAV file
        if file.content_type != "audio/wav":
            raise HTTPException(status_code=400, detail="Invalid file format. Only WAV files are supported.")

        # Save the uploaded file to disk (you can skip this if you want to keep it in memory)
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Open the WAV file for processing
        wf = wave.open(file_path, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in [8000, 16000]:
            raise HTTPException(status_code=400, detail="Audio file must be mono, 16-bit, and 8000 or 16000 Hz.")

        # Initialize the recognizer
        recognizer = KaldiRecognizer(model, wf.getframerate())
        recognizer.SetWords(True)

        # Process the audio and extract text
        text_result = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                result_dict = json.loads(result)
                text_result += result_dict.get("text", "")

        # Final result (in case some words were missed)
        final_result = recognizer.FinalResult()
        result_dict = json.loads(final_result)
        text_result += result_dict.get("text", "")

        return {"text": text_result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the audio: {str(e)}")
