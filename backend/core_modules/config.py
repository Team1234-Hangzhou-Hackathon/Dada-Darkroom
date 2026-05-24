import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai-next.com")

OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
ZHIPU_VISION_MODEL = os.getenv("ZHIPU_VISION_MODEL", "glm-4v-flash")
