import asyncio
import logging

from zhipuai import ZhipuAI

from app.config import ZHIPU_API_KEY, ZHIPU_IMAGE_MODEL

logger = logging.getLogger(__name__)
client = ZhipuAI(api_key=ZHIPU_API_KEY)
GENERATION_INTERVAL_SECONDS = 2
RATE_LIMIT_RETRY_DELAYS = (5, 10, 20)


async def generate_images(prompts: list[str]) -> list[dict]:
    images = []
    for i, prompt in enumerate(prompts):
        if i:
            await asyncio.sleep(GENERATION_INTERVAL_SECONDS)
        images.append(await _generate_with_retry(i, prompt))

    return images


async def _generate_with_retry(index: int, prompt: str) -> dict:
    for attempt in range(len(RATE_LIMIT_RETRY_DELAYS) + 1):
        try:
            return await _generate_one(prompt)
        except Exception as exc:
            is_rate_limit = "429" in str(exc) or "1302" in str(exc)
            if is_rate_limit and attempt < len(RATE_LIMIT_RETRY_DELAYS):
                delay = RATE_LIMIT_RETRY_DELAYS[attempt]
                logger.warning("Image %d rate limited; retrying in %ds", index, delay)
                await asyncio.sleep(delay)
                continue
            logger.error("Image %d generation failed: %s", index, exc)
            return {"prompt": prompt, "image_url": None, "error": str(exc)}


async def _generate_one(prompt: str) -> dict:
    response = await asyncio.to_thread(
        client.images.generations,
        model=ZHIPU_IMAGE_MODEL,
        prompt=prompt,
    )
    url = response.data[0].url
    logger.info("Generated image for prompt: %s...", prompt[:50])
    return {"prompt": prompt, "image_url": url}
