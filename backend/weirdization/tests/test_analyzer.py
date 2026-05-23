import asyncio
import json
import unittest
from types import SimpleNamespace

from app.services import analyzer


class AnalyzeMoodTests(unittest.TestCase):
    def test_uses_supported_output_limit_for_glm_4v_flash(self):
        captured = {}

        def fake_create(**kwargs):
            captured.update(kwargs)
            payload = {
                "emotion": {
                    "primary": "calm",
                    "secondary": "hopeful",
                    "intensity": 0.5,
                    "color_palette": ["blue", "gold", "white"],
                },
                "paintings": [],
            }
            message = SimpleNamespace(content=json.dumps(payload))
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        original_create = analyzer.client.chat.completions.create
        analyzer.client.chat.completions.create = fake_create
        try:
            asyncio.run(analyzer.analyze_mood("base64-image", "calm"))
        finally:
            analyzer.client.chat.completions.create = original_create

        self.assertEqual(captured["max_tokens"], 1024)


if __name__ == "__main__":
    unittest.main()
