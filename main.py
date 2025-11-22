import asyncio, websockets
from fastapi import FastAPI, Request, HTTPException
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
async def audio_transcription(websocket, path):
    async for message in websocket:
        # Process incoming audio chunk
        transcription = process_audio_chunk(message)
        await websocket.send(transcription)

        # Convert the incoming audio to WAV format using ffmpeg
start_server = websockets.serve(audio_transcription, 'localhost', 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
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
