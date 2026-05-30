import os
import tempfile
import uuid

import soundfile as sf
import sounddevice as sd

from logger import setup_logger
from config import openai_client


logger = setup_logger("snackstack.voice.speaker")

class VoiceSpeaker:
    """Convert text to speech and play it back."""

    def __init__(self, voice: str = "nova", speed: float = 1.0):
        self.voice = voice
        self.speed = speed
        self._out_dir = tempfile.gettempdir()


    def synthesize(self, text: str) -> None:
        """Synthesize text to speech and play it back."""
        out_path = os.path.join(self._out_dir, f"tts_{uuid.uuid4().hex[:8]}.mp3")
        
        try:
            response = openai_client.audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=text,
                speed=self.speed
            )
            response.stream_to_file(out_path)
            logger.info("TTS saved → %s", out_path)
            return out_path
        except Exception:
            logger.exception("TTS synthesis failed")
            return ""


    def play(self, audio_file: str) -> None:
        """Play an audio file through the default output device."""
        try:
            data, sr = sf.read(audio_file)
            sd.play(data, sr)
            sd.wait()
        except Exception:
            logger.exception("Audio playback failed")

    def speak(self, text: str, play: bool = True) -> str:
        """Synthesise text and optionally play it. Returns the file path."""
        logger.info("Agent says: %s", text[:120])
        path = self.synthesize(text)
        if play and path:
            self.play(path)
        return path