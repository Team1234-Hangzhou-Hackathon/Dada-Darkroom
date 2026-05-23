import asyncio
import logging

from openai import OpenAI

from app.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


async def generate_images(prompts: list[str]) -> list[dict]:
    tasks = [_generate_one(p) for p in prompts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    images = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error("Image %d generation failed: %s", i, result)
            images.append({"prompt": prompts[i], "image_url": None, "error": str(result)})
        else:
            images.append(result)

    return images


async def _generate_one(prompt: str) -> dict:
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        ),
    )

    image_url = response.data[0].url
    logger.info("Generated image for prompt: %s...", prompt[:50])

    return {"prompt": prompt, "image_url": image_url}
