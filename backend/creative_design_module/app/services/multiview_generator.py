"""
多视角生成服务 - 使用 GPT Image-2 API 生成 5 视角图像
"""
from __future__ import annotations

import logging
import base64
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings
from app.models.schemas import DesignFeatures

logger = logging.getLogger(__name__)

# 5 个标准视角
VIEW_ANGLES = ["front", "back", "left", "right", "top"]


class MultiViewGenerator:
    """GPT Image-2 多视角图像生成器"""

    def __init__(self):
        # 使用 OPENAI_BASE_URL 作为图片生成接口的 base URL
        self.api_url = settings.OPENAI_BASE_URL.rstrip("/") + "/images/generations"
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        self.headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

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
        logger.info(f"开始使用 GPT Image-2 生成多视角图像, session={session_id}")

        # 构建提示词
        prompt = self._build_prompt(design_features)

        # 准备参考图（base64 编码）
        image_bytes = Path(image_path).read_bytes()
        image_b64 = base64.b64encode(image_bytes).decode()
        reference_image = f"data:image/png;base64,{image_b64}"

        # 生成多视角图片
        view_paths: list[str] = []
        for angle in VIEW_ANGLES:
            try:
                view_path = await self._generate_single_view(
                    prompt=prompt,
                    reference_image=reference_image,
                    session_id=session_id,
                    angle=angle,
                )
                view_paths.append(view_path)
            except Exception as e:
                logger.error(f"生成视角 {angle} 失败: {e}")

        logger.info(f"GPT Image-2 多视角生成完成, 共 {len(view_paths)} 个视角")
        return view_paths

    async def _generate_single_view(
        self,
        prompt: str,
        reference_image: str,
        session_id: str,
        angle: str,
    ) -> str:
        """生成单个视角的图片"""
        # 根据视角调整提示词
        angle_prompts = {
            "front": "正面视角",
            "back": "背面视角",
            "left": "左侧面视角",
            "right": "右侧面视角",
            "top": "顶视图",
        }

        full_prompt = f"{prompt}, {angle_prompts[angle]}, 白色背景, 专业摄影, 高细节"

        # 调用 GPT Image-2 API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers=self.headers,  # 使用包含 Authorization 的 headers
                json={
                    "model": "gpt-image-2",
                    "prompt": full_prompt,
                    "image": [reference_image],
                    "n": 1,
                    "size": "1024x1024",
                    "response_format": "url",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()
            if not result.get("data") or not result["data"][0].get("url"):
                raise ValueError("API 返回空响应")

            # 下载图片
            temp_path = Path(settings.output_path) / "temp" / f"{session_id}_{angle}.webp"
            temp_path.parent.mkdir(parents=True, exist_ok=True)

            img_response = await client.get(result["data"][0]["url"])
            if img_response.status_code != 200:
                raise RuntimeError(f"下载图片失败: {img_response.status_code}")

            # 保存图片
            final_path = Path(settings.output_path) / session_id / "multi_views" / f"view_{angle}.png"
            final_path.parent.mkdir(parents=True, exist_ok=True)
            final_path.write_bytes(img_response.content)

            logger.info(f"  生成视角 {angle} 完成: {final_path}")
            return str(final_path)

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
            "4K 高清",
        ]
        return ", ".join(parts)


# 全局单例
multiview_generator = MultiViewGenerator()
