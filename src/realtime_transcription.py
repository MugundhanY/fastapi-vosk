import asyncio
import websockets
import json
import io
from faster_whisper import WhisperModel
import numpy as np

class RealtimeTranscriber:
    def __init__(self, model_size='tiny', device='cpu', sample_rate=16000, chunk_size=16000):
        self.model = WhisperModel(model_size, device=device)
        self.connections = set()
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size

    async def handle_client(self, websocket):
        self.connections.add(websocket)
        try:
            async for message in websocket:
                try:
                    audio_bytes = message
                    audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                    segments, info = self.model.transcribe(audio_data, language='en')
                    results = []
                    for segment in segments:
                        results.append({"text": segment.text, "start": segment.start, "end": segment.end})
                    await websocket.send(json.dumps(results))
                except Exception as e:
                    print(f"Transcription error: {e}")
                    await websocket.send(json.dumps([{"error": str(e)}]))
        except websockets.exceptions.ConnectionClosedError:
            print("Client disconnected")
        finally:
            self.connections.remove(websocket)

    async def start(self, host='0.0.0.0', port=8765):
        async with websockets.serve(self.handle_client, host, port):
            print(f"WebSocket server started on ws://{host}:{port}")
            await asyncio.Future()  # Run forever

if __name__ == '__main__':
    transcriber = RealtimeTranscriber()
    asyncio.run(transcriber.start())
