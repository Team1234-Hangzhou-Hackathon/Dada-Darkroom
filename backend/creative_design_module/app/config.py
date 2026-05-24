"""
应用配置模块 - 使用 pydantic-settings 管理环境变量
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """应用全局配置，从 .env 文件和环境变量中加载"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- OpenAI / GPT-4o ---
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # --- Meshy API (PBR 纹理生成) ---
    MESHY_API_KEY: str = ""

    # --- TRELLIS 3D 重建 API ---
    TRELLIS_API_URL: str = "http://localhost:7860"

    # --- SV3D 多视角生成 API ---
    SV3D_API_URL: str = "http://localhost:7861"

    # --- Stable Diffusion Inpainting API ---
    INPAINTING_API_URL: str = "http://localhost:7862"

    # --- 文件存储 ---
    UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent / "uploads")
    OUTPUT_DIR: str = str(Path(__file__).resolve().parent.parent / "outputs")
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def output_path(self) -> Path:
        p = Path(self.OUTPUT_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


# 全局单例
settings = Settings()
