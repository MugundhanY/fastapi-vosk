# FastAPI Vosk Speech-to-Text Service

This project provides a FastAPI-based service for speech-to-text (STT) using the Vosk API. It allows you to transcribe audio files in WAV format into text.

## Prerequisites

- Python 3.6 or higher
- `pip` for installing Python packages
- Vosk model files

# WebSocket Audio Streaming

## Overview
This application supports real-time audio transcription via a WebSocket endpoint.

## WebSocket Endpoint
- **URL**: ws://localhost:8765
- **Method**: `CONNECT`

### Sending Audio Data
Send audio data in JSON format:
```json
{
  "audio": "<base64_encoded_audio>"
}
```

### Receiving Transcriptions
The server will send partial transcripts as they are processed:
```json
{
  "transcript": "<partial_transcript>"
}
```

### Error Handling
In case of errors, the server will respond with:
```json
{
  "error": "<error_message>"
}
```

### Edge Cases
- **Network Interruptions**: The server will handle connection closures gracefully.
- **Invalid Audio Formats**: The server will respond with an error message if the audio format is not supported.