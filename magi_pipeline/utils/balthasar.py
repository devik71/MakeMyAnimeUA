import subprocess
import whisper
import torch
from pathlib import Path

class Balthasar:
    @staticmethod
    def extract_audio(video_file, audio_path):
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_file),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", str(audio_path)
        ], check=True)
        return audio_path

    @staticmethod
    def transcribe(audio_path, model_name="base", language=None, device=None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        model = whisper.load_model(model_name)
        model = model.to(device)
        options = {"fp16": device == "cuda", "verbose": True}
        if language:
            options["language"] = language
        result = model.transcribe(str(audio_path), **options)
        return result 