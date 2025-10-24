import asyncio
import websockets
import json
import io
import numpy as np
import librosa
from typing import Dict, Any
from src.stt_service import STTService

class WebSocketEndpoint:
    def __init__(self, stt_service: STTService):
        self.stt_service = stt_service

    async def process_audio_chunk(self, audio_chunk: bytes) -> str:
        try:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            # Resample to 16kHz if needed (Whisper requirement)
            if librosa.get_samplerate(io.BytesIO(audio_chunk)) != 16000:
                audio_data = librosa.resample(audio_data.astype(np.float32), sr_in=librosa.get_samplerate(io.BytesIO(audio_chunk)), sr_out=16000)
            transcription = self.stt_service.transcribe(audio_data)
            return transcription
        except Exception as e:
            print(f"Error processing audio chunk: {e}")
            return "Error: Could not process audio chunk."

    async def handle_client(self, websocket, path):
        print("Client connected")
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'audio_chunk':
                        audio_chunk = data.get('data')
                        if audio_chunk:
                            transcription = await self.process_audio_chunk(bytes(audio_chunk))
                            await websocket.send(json.dumps({"type": "partial_transcript", "text": transcription}))
                        else:
                            await websocket.send(json.dumps({"type": "error", "message": "No audio data received."}))
                    elif data.get('type') == 'end_of_stream':
                        await websocket.send(json.dumps({"type": "final_transcript", "text": "Stream ended."}))
                        break
                    else:
                        await websocket.send(json.dumps({"type": "error", "message": "Invalid message type."}))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"type": "error", "message": "Invalid JSON format."}))
                except Exception as e:
                    await websocket.send(json.dumps({"type": "error", "message": f"An unexpected error occurred: {e}"}))
        except websockets.exceptions.ConnectionClosedError:
            print("Client disconnected")
        except Exception as e:
            print(f"Error in handle_client: {e}")
        finally:
            print("Client disconnected")

    async def start_server(self, host: str, port: int):
        async with websockets.serve(self.handle_client, host, port):
            print(f"WebSocket server started on ws://{host}:{port}")
            await asyncio.Future()  # Run forever
