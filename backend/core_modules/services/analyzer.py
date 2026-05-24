import asyncio
import json
import logging

import httpx
from zhipuai import ZhipuAI

from app.config import ZHIPU_API_KEY, ZHIPU_VISION_MODEL
from app.prompts.mood_art import build_messages
from app.schemas import EmotionResult, Painting

logger = logging.getLogger(__name__)

client = ZhipuAI(
    api_key=ZHIPU_API_KEY,
    timeout=120.0,
)

MAX_RETRIES = 3


async def analyze_mood(image_b64: str, user_text: str) -> dict:
    messages = build_messages(image_b64, user_text)

    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=OPENAI_VISION_MODEL,
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
        except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
            last_err = e
            logger.warning("Attempt %d/%d failed: %s", attempt + 1, MAX_RETRIES, e)
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 * (attempt + 1))

    raise RuntimeError(f"情绪分析在 {MAX_RETRIES} 次重试后仍失败: {last_err}")


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    if not text.startswith("{"):
        start = text.index("{")
        text = text[start:]
    return json.loads(text)
