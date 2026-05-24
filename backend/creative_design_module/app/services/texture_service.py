"""
PBR 纹理服务。

当前阶段三已经使用 Meshy Text-to-3D refine 生成带材质的 GLB，
因此这里不再调用旧的 /v2/image-to-3d 纹理接口，避免 404 阻断主流程。
"""
from __future__ import annotations

import logging
from pathlib import Path

from creative_design_module.app.config import settings
from creative_design_module.app.models.schemas import MaterialSettings

logger = logging.getLogger(__name__)


class TextureService:
    """纹理处理服务"""

    def __init__(self):
        self.api_key = settings.MESHY_API_KEY

    async def generate_pbr_textures(
        self,
        mesh_path: str,
        material_settings: MaterialSettings,
        session_id: str,
    ) -> dict[str, str]:
        """
        返回 PBR 纹理路径。

        说明：
        - Meshy Text-to-3D refine 输出的 GLB 通常已经包含材质/贴图。
        - 旧代码调用的 https://api.meshy.ai/v2/image-to-3d 不存在，会返回 404。
        - 为了保证阶段三可以成功产出 raw_model.glb，这里不再强制生成单独 PBR 贴图。
        """
        mesh_file = Path(mesh_path)
        if not mesh_file.exists():
            raise FileNotFoundError(f"3D 模型文件不存在，无法处理纹理: {mesh_path}")

        output_dir = Path(settings.output_path) / session_id / "textures"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Meshy 纹理步骤已降级跳过，直接复用 Meshy 返回的 GLB 材质；"
            f"session={session_id}, material={material_settings.material_type}"
        )

        # 保持接口兼容，返回空字典，不再因为纹理阶段失败阻断整个流程
        return {}


# 全局单例
texture_service = TextureService()
