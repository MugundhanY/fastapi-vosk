# FastAPI Vosk Speech-to-Text Service

This project provides a FastAPI-based service for speech-to-text (STT) using the Vosk API. It allows you to transcribe audio files in WAV format into text.

## Prerequisites

- Python 3.6 or higher
- `pip` for installing Python packages
- Vosk model files

## API Documentation

### Streaming/WebSocket API

#### `/ws/stt` - Real-time Transcription

This WebSocket endpoint allows for real-time, continuous speech-to-text transcription. Clients send audio data, and the server streams back transcription results as they become available.

**Connection URL:**
`ws://localhost:8000/ws/stt` (or `wss://your-domain.com/ws/stt` for HTTPS)

**Client-to-Server Messages:**
Clients should send raw audio data (e.g., 16kHz, 16-bit, mono PCM) as binary WebSocket messages. The server will process these audio chunks in real-time.

**Server-to-Client Messages:**
The server sends JSON messages containing transcription results.

*   **Intermediate Results:** The server may send partial transcription results with `"final": false` as the user speaks.
*   **Final Results:** When a complete utterance is detected or a pause occurs, the server sends a final transcription with `"final": true`.

**Example Server Response:**
```json
{
  "text": "this is a partial transcription",
  "final": false
}
```
```json
{
  "text": "this is the final transcription",
  "final": true
}
```

**Client Example (Python):**

This example demonstrates how to connect to the WebSocket endpoint, send audio from a microphone (using `pyaudio`), and receive transcription results.

First, install necessary libraries:
```bash
pip install websockets pyaudio
```

Then, run the Python client:
```python
import asyncio
import websockets
import pyaudio
import json

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 8000 # Audio chunk size (e.g., 0.5 seconds of audio at 16kHz)

async def transcribe_audio():
    uri = "ws://localhost:8000/ws/stt" # Adjust if your server is elsewhere

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Connecting to WebSocket...")
    async with websockets.connect(uri) as websocket:
        print("WebSocket connected. Start speaking...")
        try:
            while True:
                # Send audio data
                data = stream.read(CHUNK)
                await websocket.send(data)

                # Receive transcription results
                response = await websocket.recv()
                result = json.loads(response)
                
                if result.get("final"):
                    print(f"Final: {result['text']}")
                else:
                    print(f"Partial: {result['text']}")

        except websockets.exceptions.ConnectionClosedOK:
            print("WebSocket connection closed normally.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print("Closing audio stream.")
            stream.stop_stream()
            stream.close()
            audio.terminate()

if __name__ == "__main__":
    asyncio.run(transcribe_audio())
```