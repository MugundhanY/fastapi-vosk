import ffmpeg
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from vosk import Model, KaldiRecognizer
import soundfile as sf
import io
import wave
import json
import subprocess

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

@app.websocket("/ws/stt")
async def websocket_transcription_endpoint(websocket: WebSocket):
    await websocket.accept()
    recognizer = None # Define recognizer before use

    try:
        # Initialize the Vosk recognizer for 16kHz, 16-bit, mono PCM audio
        # The client is expected to send audio in this format directly.
        sample_rate = 16000
        recognizer = KaldiRecognizer(model, sample_rate)
        recognizer.SetWords(True)

        while True:
            data = await websocket.receive_bytes()

            if not data:
                # Client sent empty bytes, indicating the end of the audio stream.
                # Send the final transcription result and then break the loop.
                final_result = recognizer.FinalResult()
                await websocket.send_json(json.loads(final_result))
                break

            if recognizer.AcceptWaveform(data):
                # A full phrase or segment has been recognized.
                # Send the complete result for this segment.
                result = recognizer.Result()
                await websocket.send_json(json.loads(result))
            else:
                # Only a partial recognition has occurred so far.
                # Send the current partial transcription.
                partial_result = recognizer.PartialResult()
                await websocket.send_json(json.loads(partial_result))

    except WebSocketDisconnect:
        # The client has disconnected. No explicit close or send is needed here.
        # Just break from the loop.
        print("WebSocket disconnected.")
    except Exception as e:
        # Handle any other exceptions that might occur during processing.
        print(f"An error occurred in WebSocket: {e}")
        # Optionally, you could try to send an error message back if the connection
        # is still open, but for simplicity, we just log and let the connection close.
    finally:
        # Any necessary cleanup can be done here.
        # For Vosk recognizer, no specific explicit cleanup is usually required.
        pass