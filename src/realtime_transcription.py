import asyncio
import websockets
import json
from faster_whisper import WhisperModel
import numpy as np

class RealtimeTranscriber:
    def __init__(self, model_size='tiny', device='cpu'):
        self.model = WhisperModel(model_size, device=device)
        self.connections = set()

    async def handle_client(self, websocket):
        self.connections.add(websocket)
        try:
            async for message in websocket:
                try:
                    audio_data = np.frombuffer(message, dtype=np.int16)
                    segments, info = self.model.transcribe(audio_data, beam_size=5)
                    async for segment in segments:
                        await websocket.send(json.dumps({"text": segment.text, "start": segment.start, "end": segment.end}))
                except Exception as e:
                    print(f"Error processing audio: {e}")
                    await websocket.send(json.dumps({"error": str(e)}))
        except websockets.exceptions.ConnectionClosedError:
            print("Client disconnected")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            self.connections.remove(websocket)

    async def start(self, host='0.0.0.0', port=8765):
        async with websockets.serve(self.handle_client, host, port) as server:
            print(f"WebSocket server started on ws://{host}:{port}")
            await server.wait_closed()

if __name__ == '__main__':
    transcriber = RealtimeTranscriber()
    asyncio.run(transcriber.start())
