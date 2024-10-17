import ffmpeg
from fastapi import FastAPI, Request, HTTPException
from vosk import Model, KaldiRecognizer
import soundfile as sf
import io

app = FastAPI()

# Load the Vosk model (make sure the path to your model is correct)
model = Model("vosk-model-small-en-us-0.15")

@app.post("/stt")
async def transcribe_audio(request: Request):
    try:
        # Read the raw audio data from the request body
        audio_data = await request.body()

        # Create an in-memory file object for the audio data
        audio_file = io.BytesIO(audio_data)

        # First, let's check if the incoming audio data is valid by attempting a conversion with FFmpeg
        try:
            processed_audio_file = io.BytesIO()
            
            # Using ffmpeg to convert any input to WAV format
            process = (
                ffmpeg
                .input('pipe:0', format='mp3')  # Assuming input might be MP3, adapt format if needed
                .output('pipe:1', format='wav', acodec='pcm_s16le', ac=1, ar='16000')  # Convert to 16-bit mono, 16000 Hz WAV
                .run(input=audio_data, stdout=processed_audio_file, stderr=io.StringIO(), capture_stdout=True, capture_stderr=True)
            )
            processed_audio_file.seek(0)
        except ffmpeg.Error as e:
            raise HTTPException(status_code=400, detail=f"Audio conversion failed: {str(e)}")

        # Now open the processed audio file with the wave module
        wf = wave.open(processed_audio_file, "rb")

        # Check if the WAV file format is correct (mono, 16-bit, and 16000 Hz)
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise HTTPException(status_code=400, detail="Audio file must be mono, 16-bit, and 16000 Hz.")

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
