import os
from dotenv import load_dotenv

load_dotenv()

ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_VISION_MODEL = os.getenv("ZHIPU_VISION_MODEL", "glm-4v-flash")
ZHIPU_IMAGE_MODEL = os.getenv("ZHIPU_IMAGE_MODEL", "cogview-3-flash")
