import ffmpeg
from fastapi import FastAPI
from src.stt_service import STTService
from src.websocket_endpoint import WebSocketEndpoint, Request, HTTPException
from vosk import Model, KaldiRecognizer
import soundfile as sf
import io
import wave
import json
import subprocess

app = FastAPI()
stt_service = STTService()
stt_service = STTService()
websocket_endpoint = WebSocketEndpoint(stt_service)

# Load the Vosk model (make sure the path to your model is correct)
model = Model("vosk-model-small-en-us-0.15")

@app.post("/stt")
async def transcribe_audio(request: Request):
    try:
        # Read the raw audio data from the request body
        audio_data = await request.body()

        # Create an in-memory file object for the audio data
        audio_file = io.BytesIO(audio_data)

        # Convert the incoming audio to WAV format using ffmpeg
        try:
            processed_audio_file = io.BytesIO()

            # Run ffmpeg to convert any input to WAV format
            process = (
                ffmpeg
                .input('pipe:0')  # Take input from stdin (from in-memory bytes)
                .output('pipe:1', format='wav', acodec='pcm_s16le', ac=1, ar='16000')  # Convert to 16-bit mono, 16000 Hz WAV
                .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
            )

            # Write the input audio data to stdin of ffmpeg process
            stdout, stderr = process.communicate(input=audio_data)

            # Check if the conversion failed
            if process.returncode != 0:
                raise HTTPException(status_code=400, detail=f"Audio conversion failed: {stderr.decode('utf-8')}")

            # Write the processed audio output into the in-memory file
            processed_audio_file.write(stdout)
            processed_audio_file.seek(0)

        except Exception as e:
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
