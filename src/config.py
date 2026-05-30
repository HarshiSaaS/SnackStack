import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from logger import logger

load_dotenv()

# ── Validate API key ────────────────────────────────────────

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY is missing. Copy .env.example → .env and add your key.")
    sys.exit(1)

# ── Clients ──────────────────────────────────────────────────
openai_client = OpenAI(api_key=OPENAI_API_KEY)
llm =ChatOpenAI(
    model="gpt-4o",
    temperature=0.2)

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
