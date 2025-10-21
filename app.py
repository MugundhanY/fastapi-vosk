# app.py
from flask import Flask, request, jsonify, stream_with_context, Response
from flask_sockets import Sockets
from werkzeug.utils import secure_filename
import os
import whisper
import json
import gevent

app = Flask(__name__)
sockets = Sockets(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

model = whisper.load_model("base")

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        try:
            result = model.transcribe(filepath)
            return jsonify({'text': result['text']})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid request'}), 400


@sockets.route('/stream')
def echo_socket(ws):
    try:
        while not ws.closed:
            message = ws.receive()
            if message is None:
                continue
            try:
                # Assuming message is a base64 encoded audio chunk
                import base64
                import io
                import numpy as np
                from scipy.io.wavfile import write

                audio_bytes = base64.b64decode(message)
                # Convert bytes to numpy array (assuming 16-bit PCM)
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                # Reshape to (samples, channels) - assuming mono
                audio_data = audio_data.reshape(-1, 1)

                # Create a temporary WAV file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                    temp_wav_path = temp_wav.name
                    write(temp_wav_path, 16000, audio_data)

                # Transcribe the temporary WAV file
                result = model.transcribe(temp_wav_path, word_timestamps=True)
                os.remove(temp_wav_path) # Clean up temp file

                # Send partial transcriptions
                for segment in result['segments']:
                    ws.send(json.dumps({"type": "partial", "text": segment['text'], "start": segment['start'], "end": segment['end']}))

            except Exception as e:
                ws.send(json.dumps({"type": "error", "message": str(e)}))

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        ws.close()


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
