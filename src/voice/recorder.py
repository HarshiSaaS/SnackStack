import time
import io
import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_HW_AVAILABLE = True
except ImportError:
    AUDIO_HW_AVAILABLE = False

from logger import setup_logger
from config import openai_client

logger = setup_logger("snackstack.voice.recorder")

class VoiceRecorder:
    """Record audio from the microphone."""

    def __init__(self, sample_rate: int = 16_000):
        self.sample_rate = sample_rate

    def record_voice(self, duration: int = 5,countdown: bool = True) -> np.ndarray:
        """Record *duration* seconds of mono audio."""

        if countdown:
            for i in range(3, 0, -1):
                logger.info("Recording starts in %d …", i)
                time.sleep(1)

        logger.info("Recording for %d s — speak now!", duration)
        audio = sd.rec(
            int(duration * self.sample_rate), 
            samplerate=self.sample_rate, 
            channels=1, 
            dtype=np.float32
            )
        sd.wait()
        logger.info("Recording complete")
        return audio.flatten()

    def transcribe(self, audio: np.ndarray, language: str = "en") -> str:
        """Send a numpy audio array to Whisper and return the text."""

        buf = io.BytesIO()
        if AUDIO_HW_AVAILABLE:
            sf.write(buf, audio, self.sample_rate, format="WAV")
        buf.seek(0)
        buf.name = "audio.wav"

        try:
            result = openai_client.audio.transcriptions.create(
                file=buf,
                model="whisper-1",
                language=language
            )
            return result.text.strip()
        except Exception as e:
            logger.error("Error transcribing audio: %s", e)
            return ""

    def record_and_transcribe(self, duration: int = 5) -> tuple[np.ndarray, str]:
        """Record audio and transcribe it to text."""
        audio = self.record_voice(duration)
        text = self.transcribe(audio)
        logger.info("Transcription: %s", text)
        return audio, text