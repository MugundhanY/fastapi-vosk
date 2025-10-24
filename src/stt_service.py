import whisper
import torch

class STTService:
    def __init__(self, model_name="small", device="cuda" if torch.cuda.is_available() else "cpu"):
        self.model = whisper.load_model(model_name, device=device)
        self.device = device

    def transcribe(self, audio_data, sr=16000):
        try:
            result = self.model.transcribe(audio_data, fp16=False, language="en")
            return result['text']
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
