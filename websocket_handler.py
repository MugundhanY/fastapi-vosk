import asyncio
import json
import websockets
import vosk
import sounddevice as sd
import numpy as np

class WebSocketHandler:
    def __init__(self, model_path, sample_rate=16000):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.model = vosk.Model(model_path)
        self.clients = set()

    async def transcribe_audio(self, websocket):
        try:
            rec = vosk.KaldiRecognizer(self.model, self.sample_rate)
            while True:
                message = await websocket.recv()
                if isinstance(message, str):
                    try:
                        data = json.loads(message)
                        if 'audio_chunk' in data:
                            audio_chunk = np.frombuffer(bytes.fromhex(data['audio_chunk']), dtype=np.int16)
                            if rec.AcceptWaveform(audio_chunk):
                                result = json.loads(rec.Result())
                                await websocket.send(json.dumps({"partial": result["result"]}))
                            else:
                                pass # Handle partial results if needed
                    except json.JSONDecodeError:
                        print("Invalid JSON format")
                        await websocket.send(json.dumps({"error": "Invalid JSON format"}))
                    except Exception as e:
                        print(f"Error processing audio chunk: {e}")
                        await websocket.send(json.dumps({"error": f"Error processing audio chunk: {e}"}))
                elif message is None:  # Handle connection close
                    break
                else:
                    print("Received unexpected message type")
                    await websocket.send(json.dumps({"error": "Unexpected message type"}))
        except websockets.exceptions.ConnectionClosedError:
            print("Client disconnected")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            print("Transcription session ended")

    async def handler(self, websocket, path):
        print("Client connected")
        self.clients.add(websocket)
        await self.transcribe_audio(websocket)
        self.clients.remove(websocket)

    async def start_server(self, host, port):
        async with websockets.serve(self.handler, host, port):
            print(f"WebSocket server started on ws://{host}:{port}")
            await asyncio.Future()  # Run forever

