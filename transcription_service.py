import vosk
import json
import soundfile as sf
import numpy as np

class TranscriptionService:
    def __init__(self, model_path="vosk-model-small-en-us-0.15"):
        self.model = vosk.Model(model_path)
        self.sample_rate = 16000  # Standard audio sample rate
        self.rec = None

    def start_recognition(self):
        self.rec = vosk.KaldiRecognizer(self.model, self.sample_rate)

    def transcribe_chunk(self, audio_chunk_bytes):
        if self.rec is None:
            self.start_recognition()
        try:
            # Convert bytes to numpy array
            audio_chunk = np.frombuffer(audio_chunk_bytes, dtype=np.int16)
            # Resample if needed - not implemented here for brevity, but crucial for real-world scenarios
            # Convert to float32 and normalize (Vosk expects this)
            audio_chunk = audio_chunk.astype(np.float32) / 32768.0
            if self.rec.AcceptWaveform(audio_chunk.tobytes()):
                result = json.loads(self.rec.Result())
                return result.get("text", "") # Return the recognized text
            else:
                partial_result = json.loads(self.rec.PartialResult())
                return partial_result.get("partial", "") # Return partial result
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

    def finalize_transcription(self):
        if self.rec:
            result = json.loads(self.rec.FinalResult())
            return result.get("text", "")
        return ""
