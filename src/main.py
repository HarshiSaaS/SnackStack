import uuid
import argparse

from graph import build_graph
from logger import setup_logger
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from voice import VoiceRecorder, VoiceSpeaker

logger = setup_logger("snackstack.main")

class SnackStackAssistant:
    """Wires the compiled graph to CLI and voice I/O."""

    def __init__(self, voice: str = "nova", speak: bool = False):
        self.graph = build_graph()
        self.recorder = VoiceRecorder()
        self.speaker = VoiceSpeaker(voice=voice, speed=1.05) if speak else None
        self.thread_id = str(uuid.uuid4())

    @property
    def _config(self):
        return {"configurable": {"thread_id": self.thread_id}}

    def reset(self):
        """Start a fresh conversation thread."""
        self.thread_id = str(uuid.uuid4())
        logger.info("Conversation reset (thread: %s)", self.thread_id[:8])

    def ask(self, query: str, voice_input: bool = False):
        """Process a user query and return a friendly answer."""
        result = self.graph.invoke(
            {
                "messages": [
                    HumanMessage(content=query),
                ],
                "user_query": query
            },
            self._config
        )

        snapshot = self.graph.get_state(self._config)

        for task in snapshot.tasks:
            if not getattr(task, "interrupts", None):
                continue

            for intr in task.interrupts:
                prompt = intr.value
                
                # Speak the interrupt prompt if voice is enabled
                if self.speaker:
                    self.speaker.speak(prompt)

                # Collect user response via mic or keyboard
                if voice_input:
                    logger.info("Listening for HITL response...")
                    _, user_input = self.recorder.record_and_transcribe(5)
                    user_input = user_input.strip() if user_input else "unknown"
                else:
                    user_input = input(f"\n{prompt}\nYou > ").strip() or "unknown"

            result = self.graph.invoke(
                Command(resume=user_input),
                self._config
            )

        answer = result.get("final_answer", "Sorry, I could not process your request.")

        if self.speaker:
            self.speaker.speak(answer)

        return answer

    def listen_and_ask(self, duration: int = 5) -> tuple[str, str]:
        """Record from mic, transcribe, then run through the graph."""

        _, text = self.recorder.record_and_transcribe(duration)
        if not text:
            return "", "Sorry, I didn't catch that. Please try again."
        return text, self.ask(text, voice_input=True)

    

    def run_text_loop(assistant: SnackStackAssistant):
        """REPL: type queries, get agent responses."""
        logger.info("SnackStack — Text mode")
        logger.info("Type a query and press Enter. Commands: reset | quit")

        while True:
            try:
                query = input("You > ")
            except (EOFError, KeyboardInterrupt):
                break

            if not query:
                continue
            if query.lower() in ("quit", "exit", "q"):
                break
            if query.lower() == "reset":
                assistant.reset()
                continue
            
            answer = assistant.ask(query)
            print(f"\nAssistant > {answer}")
        
        logger.info("Exiting text loop")

    def run_voice_loop(assistant: SnackStackAssistant, duration: int = 5):
        """REPL: speak queries, hear agent responses."""
        logger.info("SnackStack — Voice mode")
        logger.info("Press Enter to record (%ds). Commands: reset | quit", duration)

        while True:
            try:
                cmd = input("\n[Enter] to record, 'quit' to exit > ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if cmd.lower() in ("quit", "exit", "q"):
                break
            if cmd.lower() == "reset":
                assistant.reset()
                continue

            user_text, answer = assistant.listen_and_ask(duration)
            if user_text:
                logger.info("You said: %s", user_text)
            logger.info("SnackStack: %s", answer)

        logger.info("Goodbye — stay hungry!")
        

def main() -> None:
    parser = argparse.ArgumentParser(description="SnackStack Voice Assistant")
    parser.add_argument("--voice",     action="store_true", help="Full voice: mic + speaker")
    parser.add_argument("--voice-out", action="store_true", help="Text input + voice output")
    parser.add_argument("--tts-voice", default="nova",      help="TTS voice (default: nova)")
    args = parser.parse_args()

    speak = args.voice or args.voice_out

    if args.voice:
        assistant = SnackStackAssistant(voice=args.tts_voice, speak=speak)
        assistant.run_voice_loop()
    else:
        assistant = SnackStackAssistant()
        assistant.run_text_loop()


if __name__ == "__main__":
    main()