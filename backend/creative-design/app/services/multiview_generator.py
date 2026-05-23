"""
多视角生成服务 - 调用 SV3D API 生成 5 视角图像
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings
from app.models.schemas import DesignFeatures

logger = logging.getLogger(__name__)

# 5 个标准视角
VIEW_ANGLES = ["front", "back", "left", "right", "top"]
VIEW_ELEVATIONS = {
    "front": 0.0,
    "back": 0.0,
    "left": 0.0,
    "right": 0.0,
    "top": 90.0,
}
VIEW_AZIMUTHS = {
    "front": 0.0,
    "back": 180.0,
    "left": 90.0,
    "right": 270.0,
    "top": 0.0,
}


class MultiViewGenerator:
    """SV3D 多视角图像生成器"""

    def __init__(self):
        self.api_url = settings.SV3D_API_URL.rstrip("/")
        self.timeout = httpx.Timeout(300.0, connect=30.0)

    def _build_prompt(self, design_features: DesignFeatures) -> str:
        """根据设计特征构建多视角生成提示词"""
        parts = [
            design_features.style_description,
            f"材质: {design_features.material_guess}",
            f"色调: {', '.join(design_features.primary_colors[:3])}",
            "工业设计产品渲染图",
            "白色背景",
            "专业摄影",
            "高细节",
        ]
        return ", ".join(parts)

    async def generate_multi_view(
        self,
        image_path: str,
        design_features: DesignFeatures,
        session_id: str,
    ) -> list[str]:
        """
        从灵感图像生成 5 个标准视角的图像。

        Args:
            image_path: 灵感图像路径
            design_features: 设计特征（用于增强提示词）
            session_id: 会话 ID

        Returns:
            5 个视角图像的文件路径列表
        """
        logger.info(f"开始生成多视角图像, session={session_id}")

        prompt = self._build_prompt(design_features)
        output_dir = Path(settings.output_path) / session_id / "multi_views"
        output_dir.mkdir(parents=True, exist_ok=True)

        view_paths: list[str] = []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 读取原图并编码
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            for angle in VIEW_ANGLES:
                try:
                    # 调用 SV3D API 生成单视角
                    files = {
                        "image": ("image.png", image_bytes, "image/png"),
                    }
                    data = {
                        "prompt": prompt,
                        "elevation": str(VIEW_ELEVATIONS[angle]),
                        "azimuth": str(VIEW_AZIMUTHS[angle]),
                    }

                    response = await client.post(
                        f"{self.api_url}/generate",
                        files=files,
                        data=data,
                    )
                    response.raise_for_status()

                    # 保存生成的视角图像
                    output_filename = f"view_{angle}.png"
                    output_path = output_dir / output_filename
                    output_path.write_bytes(response.content)
                    view_paths.append(str(output_path))

                    logger.info(f"  生成视角 {angle} 完成: {output_path}")

                except httpx.HTTPError as e:
                    logger.error(f"  生成视角 {angle} 失败: {e}")
                    # 降级：复制原图作为该视角
                    fallback_path = output_dir / f"view_{angle}.png"
                    import shutil
                    shutil.copy2(image_path, fallback_path)
                    view_paths.append(str(fallback_path))

        logger.info(f"多视角生成完成, 共 {len(view_paths)} 个视角")
        return view_paths

    async def regenerate_single_view(
        self,
        base_image_path: str,
        design_features: DesignFeatures,
        view_index: int,
        session_id: str,
    ) -> str:
        """重新生成单个视角"""
        angle = VIEW_ANGLES[view_index % len(VIEW_ANGLES)]
        prompt = self._build_prompt(design_features)
        output_dir = Path(settings.output_path) / session_id / "multi_views"
        output_dir.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            with open(base_image_path, "rb") as f:
                image_bytes = f.read()

            files = {"image": ("image.png", image_bytes, "image/png")}
            data = {
                "prompt": prompt,
                "elevation": str(VIEW_ELEVATIONS[angle]),
                "azimuth": str(VIEW_AZIMUTHS[angle]),
            }

            response = await client.post(
                f"{self.api_url}/generate",
                files=files,
                data=data,
            )
            response.raise_for_status()

            output_path = output_dir / f"view_{angle}.png"
            output_path.write_bytes(response.content)
            return str(output_path)


# 全局单例
multiview_generator = MultiViewGenerator()
