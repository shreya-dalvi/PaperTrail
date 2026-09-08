import os
import logging
from dotenv import load_dotenv
from groq import Groq, NotFoundError
from src.config import GROQ_MODEL, GROQ_FALLBACK_MODEL

load_dotenv()  # must run before Groq() reads GROQ_API_KEY from the environment

logger = logging.getLogger(__name__)
client = Groq()

def call_groq(messages, **kwargs):
    """
    Wraps Groq chat completion calls with automatic fallback
    if the primary model has been deprecated/removed.
    """
    try:
        return client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            **kwargs
        )
    except NotFoundError:
        logger.warning(
            f"Model '{GROQ_MODEL}' not found (likely deprecated). "
            f"Falling back to '{GROQ_FALLBACK_MODEL}'."
        )
        return client.chat.completions.create(
            model=GROQ_FALLBACK_MODEL,
            messages=messages,
            **kwargs
        )