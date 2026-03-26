import asyncio
import websockets
import json
import wave
import audioop
import os
import sys
from pathlib import Path

# --- Configuration ---
# Replace with the actual WebSocket URL of your streaming transcription server
WEBSOCKET_URL = "ws://localhost:8000/stream"
# Audio parameters (adjust if your server expects different values)
SAMPLE_RATE = 16000  # Hz
CHANNELS = 1         # Mono
SAMPLE_WIDTH = 2     # 2 bytes per sample (16-bit)
CHUNK_SIZE = 1024    # Number of frames per audio chunk

# --- Helper Functions ---

async def send_audio_stream(websocket: websockets.WebSocketClientProtocol, audio_file_path: Path):
    """
    Reads an audio file, processes it, and streams it to the WebSocket server.
    Sends an initial metadata message and then continuous audio chunks.
    """
    try:
        with wave.open(str(audio_file_path), 'rb') as wf:
            if wf.getnchannels() != CHANNELS or wf.getsampwidth() != SAMPLE_WIDTH or wf.getframerate() != SAMPLE_RATE:
                print(f"Warning: Audio file parameters ({wf.getnchannels()} channels, {wf.getsampwidth()}-byte sample width, {wf.getframerate()} Hz) "
                      f"do not match expected ({CHANNELS} channels, {SAMPLE_WIDTH}-byte sample width, {SAMPLE_RATE} Hz). "
                      f"Attempting conversion.")
                # Read all frames for conversion
                original_frames = wf.readframes(wf.getnframes())
                
                # Convert to mono if necessary
                if wf.getnchannels() > CHANNELS:
                    original_frames = audioop.tomono(original_frames, wf.getsampwidth(), 1, 1)
                
                # Convert sample width if necessary
                if wf.getsampwidth() != SAMPLE_WIDTH:
                    original_frames = audioop.lin2lin(original_frames, wf.getsampwidth(), SAMPLE_WIDTH)
                
                # Resample if necessary (this is more complex and often done server-side or with a dedicated library like `resampy`)
                # For simplicity, this example assumes the server can handle slight mismatches or that the input is close enough.
                # A proper resampler would be needed here for accurate sample rate conversion.
                if wf.getframerate() != SAMPLE_RATE:
                    print(f"Warning: Resampling from {wf.getframerate()} Hz to {SAMPLE_RATE} Hz is not fully implemented in this client example. "
                          f"The server might need to handle this or you might need to pre-process your audio.")
                
                # Use the converted frames for streaming
                audio_data_to_stream = original_frames
                current_pos = 0

                # Send initial metadata message
                await websocket.send(json.dumps({
                    "type": "start",
                    "audio_format": {
                        "sample_rate": SAMPLE_RATE,
                        "channels": CHANNELS,
                        "sample_width": SAMPLE_WIDTH,
                        "encoding": "linear16" # Common encoding for raw PCM
                    }
                }))
                print("Sent 'start' message with audio metadata.")

                while current_pos < len(audio_data_to_stream):
                    chunk = audio_data_to_stream[current_pos : current_pos + CHUNK_SIZE * SAMPLE_WIDTH * CHANNELS]
                    if not chunk:
                        break
                    await websocket.send(chunk)
                    current_pos += len(chunk)
                    await asyncio.sleep(0.01) # Small delay to simulate real-time streaming
                
            else:
                # Audio file matches expected parameters, stream directly
                # Send initial metadata message
                await websocket.send(json.dumps({
                    "type": "start",
                    "audio_format": {
                        "sample_rate": SAMPLE_RATE,
                        "channels": CHANNELS,
                        "sample_width": SAMPLE_WIDTH,
                        "encoding": "linear16" # Common encoding for raw PCM
                    }
                }))
                print("Sent 'start' message with audio metadata.")

                while True:
                    chunk = wf.readframes(CHUNK_SIZE)
                    if not chunk:
                        break
                    await websocket.send(chunk)
                    await asyncio.sleep(0.01) # Small delay to simulate real-time streaming

        # Send an 'end' message to signal the completion of the audio stream
        await websocket.send(json.dumps({"type": "end"}))
        print("Sent 'end' message, audio stream concluded.")

    except FileNotFoundError:
        print(f"Error: Audio file not found at {audio_file_path}")
        raise
    except wave.Error as e:
        print(f"Error reading WAV file: {e}")
        raise
    except Exception as e:
        print(f"An error occurred during audio streaming: {e}")
        raise

async def receive_transcripts(websocket: websockets.WebSocketClientProtocol):
    """
    Receives and prints transcription results from the WebSocket server.
    Handles both partial and final results.
    """
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "partial":
                    print(f"Partial Transcript: {data.get('transcript')}")
                elif data.get("type") == "final":
                    print(f"Final Transcript: {data.get('transcript')}")
                    # Optionally, break here if the server closes the connection after final
                    # Or continue if the server might send more messages (e.g., for multiple segments)
                elif data.get("type") == "error":
                    print(f"Server Error: {data.get('message')}")
                else:
                    print(f"Received unknown message type: {data}")
            except json.JSONDecodeError:
                print(f"Received non-JSON message: {message}")
    except websockets.exceptions.ConnectionClosedOK:
        print("WebSocket connection closed gracefully by the server.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"WebSocket connection closed with error: {e}")
    except Exception as e:
        print(f"An error occurred while receiving transcripts: {e}")

async def stream_transcription_client(audio_file_path: Path):
    """
    Connects to the WebSocket server, streams audio, and receives transcripts.
    """
    print(f"Connecting to WebSocket server at {WEBSOCKET_URL}...")
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("WebSocket connection established.")
            
            # Create tasks for sending audio and receiving transcripts concurrently
            send_task = asyncio.create_task(send_audio_stream(websocket, audio_file_path))
            receive_task = asyncio.create_task(receive_transcripts(websocket))

            # Wait for both tasks to complete
            await asyncio.gather(send_task, receive_task)

    except websockets.exceptions.InvalidURI as e:
        print(f"Error: Invalid WebSocket URI: {e}")
    except websockets.exceptions.WebSocketException as e:
        print(f"WebSocket connection error: {e}")
    except ConnectionRefusedError:
        print(f"Error: Connection refused. Is the server running at {WEBSOCKET_URL}?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Main Execution ---

if __name__ == "__main__":
    # Example usage:
    # 1. Ensure you have a WAV audio file.
    #    You can create one using `ffmpeg` or record one.
    #    Example: `ffmpeg -i input.mp3 -ar 16000 -ac 1 -acodec pcm_s16le output.wav`
    #    Or download a sample: `wget https://www2.cs.uic.edu/~i101/Labs/audio.wav -O sample.wav`
    
    # Define the path to your audio file
    # For demonstration, let's assume 'sample.wav' is in the same directory
    # or specify a full path.
    
    # If no argument is provided, try a default file
    if len(sys.argv) > 1:
        audio_file = Path(sys.argv[1])
    else:
        audio_file = Path("sample.wav")
        print(f"No audio file specified. Attempting to use default: {audio_file}")
        print("Usage: python websocket_client.py <path_to_audio_file.wav>")
        print("Ensure 'sample.wav' exists or provide a valid path.")
        
        # Create a dummy WAV file if it doesn't exist for testing purposes
        if not audio_file.exists():
            print(f"Creating a dummy '{audio_file}' for demonstration...")
            try:
                with wave.open(str(audio_file), 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(SAMPLE_WIDTH)
                    wf.setframerate(SAMPLE_RATE)
                    # Write 1 second of silence
                    wf.writeframes(b'\x00' * SAMPLE_RATE * CHANNELS * SAMPLE_WIDTH)
                print(f"Dummy '{audio_file}' created. It contains silence.")
                print("For actual transcription, replace it with a WAV file containing speech.")
            except Exception as e:
                print(f"Could not create dummy WAV file: {e}")
                sys.exit(1)

    if not audio_file.exists():
        print(f"Error: Audio file '{audio_file}' not found. Please provide a valid path.")
        sys.exit(1)

    # Run the asynchronous client
    asyncio.run(stream_transcription_client(audio_file))