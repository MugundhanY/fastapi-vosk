import asyncio
import websockets
import json
from transcription_service import TranscriptionService

class WebSocketHandler:
    def __init__(self, transcription_service: TranscriptionService, host="localhost", port=8765):
        self.transcription_service = transcription_service
        self.host = host
        self.port = port
        self.server = None

    async def handle_client(self, websocket, path):
        print("Client connected")
        try:
            self.transcription_service.start_recognition()
            async for message in websocket:
                try:
                    if isinstance(message, bytes):
                        partial_transcript = self.transcription_service.transcribe_chunk(message)
                        if partial_transcript:
                            await websocket.send(json.dumps({"type": "partial", "text": partial_transcript}))
                    elif isinstance(message, str):
                        if message == "close":
                            break
                        else:
                            print(f"Received unexpected message: {message}")
                except Exception as e:
                    print(f"Error processing message: {e}")
                    await websocket.send(json.dumps({"type": "error", "message": str(e)}))
                    break
            final_transcript = self.transcription_service.finalize_transcription()
            if final_transcript:
                await websocket.send(json.dumps({"type": "final", "text": final_transcript}))
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection closed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            print("Client disconnected")

    async def start_server(self):
        self.server = await websockets.serve(self.handle_client, self.host, self.port)
        print(f"WebSocket server started at ws://{self.host}:{self.port}")
        return self.server

    async def stop_server(self):
        if self.server and self.server.is_serving():
            self.server.close()
            await self.server.wait_closed()
            print("WebSocket server stopped")
