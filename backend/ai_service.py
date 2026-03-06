import os
import logging
from fastapi import HTTPException
from groq import Groq

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not set – AI features will fail at runtime.")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

MODEL        = "llama-3.3-70b-versatile"
TEMPERATURE  = 0.3
MAX_TOKENS   = 2000
TOP_P        = 0.9

def call_groq(prompt: str) -> str:
    """Send a prompt to Groq and return the response text."""
    if not groq_client:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is not configured. Please set it in the .env file.",
        )
    try:
        completion = groq_client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert senior software engineer and security researcher "
                        "specializing in code review, performance optimization, and secure coding practices. "
                        "Always respond in well-structured Markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            top_p=TOP_P,
        )
        return completion.choices[0].message.content
    except Exception as exc:
        logger.error("Groq API error: %s", exc)
        raise HTTPException(status_code=502, detail=f"AI service error: {str(exc)}")
