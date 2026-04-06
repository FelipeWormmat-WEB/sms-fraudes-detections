import logging
import os

from openai import OpenAI

logger = logging.getLogger("llm_service")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

SYSTEM_PROMPT = (
    "You classify SMS text for fraud detection. "
    "Reply with exactly one token: spam or ham."
)


def _normalize_prediction(value: str) -> str:
    content = (value or "").strip().lower()
    if "spam" in content or "fraud" in content or "scam" in content:
        return "spam"
    if "ham" in content or "legit" in content or "safe" in content:
        return "ham"
    return "unknown"


def generate_response(prompt: str, max_tokens: int = 16) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY is missing")
        return "unknown"

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        return _normalize_prediction(content)
    except Exception as exc:
        logger.error("OpenAI request failed: %s", exc)
        return "unknown"
