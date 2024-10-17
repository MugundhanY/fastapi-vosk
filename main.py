import librosa
import soundfile as sf
from fastapi import FastAPI, Request, HTTPException
from vosk import Model, KaldiRecognizer
import io

app = FastAPI()

# Load the Vosk model (make sure the path to your model is correct)
model = Model("vosk-model-small-en-us-0.15")

@app.post("/stt/")
async def transcribe_audio(request: Request):
    try:
        # Read the raw audio data from the request body
        audio_data = await request.body()

        # Create an in-memory file object
        audio_file = io.BytesIO(audio_data)

        # Load the audio with librosa, this will also handle non-WAV formats
        y, sr = librosa.load(audio_file, sr=16000)

        # Create a new BytesIO object to store the properly formatted audio
        processed_audio_file = io.BytesIO()

        # Write the corrected audio to the new BytesIO object as a WAV file
        sf.write(processed_audio_file, y, sr, format='WAV')
        processed_audio_file.seek(0)

        # Now open the processed audio file with wave module
        wf = wave.open(processed_audio_file, "rb")

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
