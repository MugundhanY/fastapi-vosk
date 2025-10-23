# Real-time Transcription API

## WebSocket Endpoint

*   **Endpoint:** `ws://<host>:<port>` (e.g., `ws://localhost:8765`)
*   **Method:** WebSocket

## Usage

1.  **Connect:** Establish a WebSocket connection to the endpoint.
2.  **Send Audio:** Send raw audio data as binary data (bytes).  The audio should be in 16kHz, mono, 16-bit PCM format.
3.  **Receive Transcriptions:** Receive JSON objects containing partial and final transcriptions.

## Request

*   **Format:** Raw audio data (bytes)

## Response

*   **Format:** JSON
*   **Example:**
    ```json
    {"text": "hello", "start": 0.1, "end": 0.5}
    ```
    ```json
    {"text": "world", "start": 0.6, "end": 1.0}
    ```

## Error Handling

*   If an error occurs during audio processing, the server will send a JSON object with an `error` key.
    ```json
    {"error": "Transcription failed"}
    ```

## Example Client (Python)

```python
import asyncio
import websockets
import numpy as np

async def transcribe_audio(host='localhost', port=8765):
    uri = f"ws://{host}:{port}"
    try:
        async with websockets.connect(uri) as websocket:
            # Simulate sending audio data (replace with actual audio streaming)
            for i in range(5):
                # Generate some dummy audio data (1 second at 16kHz)
                audio_data = np.random.randint(-32768, 32767, 16000, dtype=np.int16).tobytes()
                await websocket.send(audio_data)
                await asyncio.sleep(1) # Simulate sending data every second

            print("Finished sending audio")
            # Optionally, send a close frame
            # await websocket.close()

            async for message in websocket:
                print(f"Received: {message}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(transcribe_audio())
```
