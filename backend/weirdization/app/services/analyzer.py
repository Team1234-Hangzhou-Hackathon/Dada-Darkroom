import json
import logging

from zhipuai import ZhipuAI

from app.config import ZHIPU_API_KEY, ZHIPU_VISION_MODEL
from app.prompts.mood_art import build_messages
from app.schemas import EmotionResult, Painting

logger = logging.getLogger(__name__)

client = ZhipuAI(api_key=ZHIPU_API_KEY)


async def analyze_mood(image_b64: str, user_text: str) -> dict:
    messages = build_messages(image_b64, user_text)

    response = client.chat.completions.create(
        model=ZHIPU_VISION_MODEL,
        messages=messages,
        max_tokens=1024,
        temperature=0.8,
    )

    raw = response.choices[0].message.content
    logger.info("GLM-4V raw response: %s", raw)

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
