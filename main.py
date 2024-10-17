from fastapi import FastAPI, Request, HTTPException
from vosk import Model, KaldiRecognizer
import soundfile as sf
import io

app = FastAPI()

# Load the Vosk model (make sure the path to your model is correct)
model = Model("vosk-model-small-en-us-0.15")

@app.post("/stt/")
async def transcribe_audio(request: Request):
    try:
        # Read the raw audio data from the request body
        audio_data = await request.body()

        # Create an in-memory file object for the audio data
        audio_file = io.BytesIO(audio_data)

        # Use soundfile to read the audio data from the in-memory file object
        try:
            audio, samplerate = sf.read(audio_file)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid or unsupported audio format: {str(e)}")

        # Resample the audio to 16000 Hz (if needed)
        if samplerate != 16000:
            audio = librosa.resample(audio, orig_sr=samplerate, target_sr=16000)
            samplerate = 16000

        # Write the resampled audio to a new BytesIO object as a WAV file
        processed_audio_file = io.BytesIO()
        sf.write(processed_audio_file, audio, samplerate, format='WAV')
        processed_audio_file.seek(0)

        # Now open the processed audio file with the wave module
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
