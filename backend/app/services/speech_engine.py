import tempfile
from pathlib import Path
from typing import Any


class SpeechEngine:
    async def synthesize(self, text: str, voice: str) -> dict[str, Any]:
        try:
            import edge_tts
        except Exception:
            return {"ok": False, "message": "edge-tts is not installed."}

        target = Path(tempfile.gettempdir()) / "jarvis-tts.mp3"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(target))
        return {"ok": True, "path": str(target)}

    def transcribe(self, audio_path: str, language: str = "auto") -> dict[str, Any]:
        try:
            from faster_whisper import WhisperModel
        except Exception:
            return {"ok": False, "message": "faster-whisper is not installed."}

        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _info = model.transcribe(audio_path, language=None if language == "auto" else language)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return {"ok": True, "text": text}
