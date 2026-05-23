import unittest

from app.prompts.mood_art import SYSTEM_PROMPT


class MoodArtPromptTests(unittest.TestCase):
    def test_requests_compact_output_that_fits_flash_model_limit(self):
        self.assertIn("20-30词", SYSTEM_PROMPT)
        self.assertNotIn("50-80", SYSTEM_PROMPT)
        self.assertNotIn('"variation"', SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
