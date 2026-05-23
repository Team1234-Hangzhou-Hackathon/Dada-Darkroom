import asyncio
import unittest
from types import SimpleNamespace

from app.config import ZHIPU_IMAGE_MODEL
from app.services import generator


class GenerateImagesTests(unittest.TestCase):
    def test_uses_configured_zhipu_image_model(self):
        captured = {}

        def fake_generations(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                data=[SimpleNamespace(url="https://images.example/generated.png")]
            )

        original_generations = generator.client.images.generations
        generator.client.images.generations = fake_generations
        try:
            images = asyncio.run(generator.generate_images(["abstract painting"]))
        finally:
            generator.client.images.generations = original_generations

        self.assertEqual(captured["model"], ZHIPU_IMAGE_MODEL)
        self.assertEqual(
            images,
            [
                {
                    "prompt": "abstract painting",
                    "image_url": "https://images.example/generated.png",
                }
            ],
        )

    def test_retries_a_temporarily_rate_limited_generation(self):
        attempts = 0
        delays = []

        def flaky_generations(**kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("429 rate limited")
            return SimpleNamespace(
                data=[SimpleNamespace(url="https://images.example/retried.png")]
            )

        async def fake_sleep(seconds):
            delays.append(seconds)

        original_generations = generator.client.images.generations
        original_sleep = generator.asyncio.sleep
        generator.client.images.generations = flaky_generations
        generator.asyncio.sleep = fake_sleep
        try:
            images = asyncio.run(generator.generate_images(["abstract painting"]))
        finally:
            generator.client.images.generations = original_generations
            generator.asyncio.sleep = original_sleep

        self.assertEqual(attempts, 2)
        self.assertEqual(images[0]["image_url"], "https://images.example/retried.png")
        self.assertTrue(delays)

    def test_spaces_consecutive_generation_requests(self):
        delays = []

        def fake_generations(**kwargs):
            return SimpleNamespace(
                data=[SimpleNamespace(url="https://images.example/generated.png")]
            )

        async def fake_sleep(seconds):
            delays.append(seconds)

        original_generations = generator.client.images.generations
        original_sleep = generator.asyncio.sleep
        generator.client.images.generations = fake_generations
        generator.asyncio.sleep = fake_sleep
        try:
            asyncio.run(generator.generate_images(["first painting", "second painting"]))
        finally:
            generator.client.images.generations = original_generations
            generator.asyncio.sleep = original_sleep

        self.assertTrue(delays)


if __name__ == "__main__":
    unittest.main()
