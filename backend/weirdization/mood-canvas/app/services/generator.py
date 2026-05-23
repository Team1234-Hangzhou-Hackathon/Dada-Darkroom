import asyncio
import logging

from zhipuai import ZhipuAI

from app.config import ZHIPU_API_KEY, ZHIPU_IMAGE_MODEL

logger = logging.getLogger(__name__)

client = ZhipuAI(
    api_key=ZHIPU_API_KEY,
    timeout=120.0,
)

MAX_RETRIES = 2


async def generate_images(prompts: list[str]) -> list[dict]:
    images = []
    for i, prompt in enumerate(prompts):
        last_err = None
        for attempt in range(MAX_RETRIES):
            try:
                result = await _generate_one(prompt)
                images.append(result)
                break
            except Exception as exc:
                last_err = exc
                logger.warning("Image %d attempt %d failed: %s", i, attempt + 1, exc)
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(3)
        else:
            logger.error("Image %d generation failed after %d retries: %s", i, MAX_RETRIES, last_err)
            images.append({"prompt": prompt, "image_url": None, "error": str(last_err)})

    return images


async def _generate_one(prompt: str) -> dict:
    response = await asyncio.to_thread(
        client.images.generations,
        model=ZHIPU_IMAGE_MODEL,
        prompt=prompt,
    )
    url = response.data[0].url
    logger.info("Generated image for prompt: %s...", prompt[:50])
    return {"prompt": prompt, "image_url": url}
