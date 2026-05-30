import logging
import sys

def setup_logger(name: str) -> logging.Logger:
    """Setup the logger for the project."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.info(f"Logger {name} setup successfully")
    return logger

logger = setup_logger("SnackStack-voice-agent")