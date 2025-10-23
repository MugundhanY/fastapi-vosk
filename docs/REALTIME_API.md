# Real-time Transcription API

## WebSocket Endpoint

*   **Endpoint:** `ws://<your_server_address>:<port>` (e.g., `ws://localhost:8765`)
*   **Port:** 8765 (default)

## Usage

1.  **Connect:** Establish a WebSocket connection to the endpoint.
2.  **Send Audio:** Send raw audio data as bytes. The audio should be:
    *   16kHz
    *   Mono
    *   16-bit PCM
3.  **Receive Transcriptions:** The server will return JSON-formatted transcriptions as they are generated.

## Response Format

```json
[{
    "text": "transcribed text",
    "start": 0.0,  // Start time in seconds
    "end": 1.0    // End time in seconds
}, ...]
```

## Example Client (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
  console.log('Connected to WebSocket');
  // Example: Send some dummy audio data
  const audioData = new Int16Array(16000); // 1 second of silence at 16kHz
  ws.send(audioData.buffer);
};

ws.onmessage = (event) => {
  const transcriptions = JSON.parse(event.data);
  console.log('Transcriptions:', transcriptions);
};

ws.onclose = () => {
  console.log('Disconnected from WebSocket');
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```