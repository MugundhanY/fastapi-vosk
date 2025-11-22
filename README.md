# Real-Time Audio Transcription via WebSocket

## Usage Example

To connect to the WebSocket server:

```python
import asyncio
import websockets

async def transcribe_audio():
    async with websockets.connect('ws://localhost:8765') as websocket:
        with open('audio_chunk.wav', 'rb') as audio_file:
            audio_data = audio_file.read(1024)  # Read in chunks
            await websocket.send(audio_data)
            response = await websocket.recv()
            print(response)

asyncio.run(transcribe_audio())
```

This project provides a FastAPI-based service for speech-to-text (STT) using the Vosk API. It allows you to transcribe audio files in WAV format into text.

## Prerequisites

- Python 3.6 or higher
- `pip` for installing Python packages
- Vosk model files

