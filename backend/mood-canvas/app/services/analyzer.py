import json
import logging

from openai import OpenAI

from app.config import OPENAI_API_KEY
from app.prompts.mood_art import build_messages
from app.schemas import EmotionResult, Painting

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


async def analyze_mood(image_b64: str, user_text: str) -> dict:
    messages = build_messages(image_b64, user_text)

    response = client.chat.completions.create(
        model="gpt-5.5",
        messages=messages,
        max_tokens=2000,
        temperature=0.8,
    )

    raw = response.choices[0].message.content
    logger.info("GPT-5.5 raw response: %s", raw)

    parsed = _extract_json(raw)

    emotion = EmotionResult(**parsed["emotion"])
    paintings = [Painting(**p) for p in parsed["paintings"]]

    return {"emotion": emotion, "paintings": paintings}


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    if not text.startswith("{"):
        start = text.index("{")
        text = text[start:]
    return json.loads(text)
