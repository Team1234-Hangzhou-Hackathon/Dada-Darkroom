"""
Inpainting 服务 - Stable Diffusion 图像修复与风格传播
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image
import numpy as np
import io

from app.config import settings

logger = logging.getLogger(__name__)


class InpaintingService:
    """Stable Diffusion Inpainting 服务"""

    def __init__(self):
        self.api_url = settings.INPAINTING_API_URL.rstrip("/")
        self.timeout = httpx.Timeout(300.0, connect=30.0)

    async def inpaint_view(
        self,
        view_path: str,
        mask_path: str,
        prompt: str,
        session_id: str,
    ) -> str:
        """
        对指定视角图像执行 inpainting。

        Args:
            view_path: 原始视角图像路径
            mask_path: 蒙版图像路径（白色区域为需要重绘的区域）
            prompt: 修改提示词
            session_id: 会话 ID

        Returns:
            修改后的图像路径
        """
        logger.info(f"开始 inpainting, view={view_path}, prompt={prompt}")

        output_dir = Path(settings.output_path) / session_id / "modified_views"
        output_dir.mkdir(parents=True, exist_ok=True)

        view_name = Path(view_path).stem
        output_path = output_dir / f"{view_name}_modified.png"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            with open(view_path, "rb") as vf, open(mask_path, "rb") as mf:
                files = {
                    "image": ("image.png", vf.read(), "image/png"),
                    "mask": ("mask.png", mf.read(), "image/png"),
                }
                data = {
                    "prompt": prompt,
                    "negative_prompt": "low quality, blurry, distorted, deformed",
                    "denoising_strength": "0.75",
                    "inpainting_fill": "1",  # 原图填充
                    "inpainting_full_res": "true",
                }

                try:
                    response = await client.post(
                        f"{self.api_url}/sdapi/v1/img2img",
                        files=files,
                        data=data,
                    )
                    response.raise_for_status()

                    result = response.json()
                    # 从 base64 解码图像
                    image_data = result.get("images", [None])[0]
                    if image_data:
                        import base64
                        img_bytes = base64.b64decode(image_data)
                        output_path.write_bytes(img_bytes)
                    else:
                        # 如果返回的是二进制
                        output_path.write_bytes(response.content)

                    logger.info(f"Inpainting 完成: {output_path}")
                    return str(output_path)

                except httpx.HTTPError as e:
                    logger.error(f"Inpainting API 调用失败: {e}")
                    raise RuntimeError(f"Inpainting 服务调用失败: {e}") from e

    async def propagate_changes(
        self,
        modified_view_path: str,
        other_view_paths: list[str],
        prompt: str,
        session_id: str,
    ) -> list[str]:
        """
        将修改传播到其他视角，保持风格一致性。

        使用 ControlNet + IP-Adapter 实现跨视角风格传播。
        对每个其他视角，以修改后的图像作为风格参考进行轻量级重绘。

        Args:
            modified_view_path: 已修改的视角图像路径
            other_view_paths: 其他视角图像路径列表
            prompt: 修改提示词
            session_id: 会话 ID

        Returns:
            更新后的所有视角路径列表（包含修改后的视角）
        """
        logger.info(f"开始风格传播, 源={modified_view_path}, 目标数={len(other_view_paths)}")

        output_dir = Path(settings.output_path) / session_id / "modified_views"
        output_dir.mkdir(parents=True, exist_ok=True)

        updated_paths: list[str] = [modified_view_path]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            with open(modified_view_path, "rb") as ref_f:
                ref_image_bytes = ref_f.read()

            for other_path in other_view_paths:
                try:
                    view_name = Path(other_path).stem
                    output_path = output_dir / f"{view_name}_propagated.png"

                    with open(other_path, "rb") as of:
                        files = {
                            "image": ("image.png", of.read(), "image/png"),
                            "reference": ("reference.png", ref_image_bytes, "image/png"),
                        }
                        data = {
                            "prompt": prompt,
                            "negative_prompt": "low quality, blurry, inconsistent style",
                            "denoising_strength": "0.35",  # 低强度以保持结构
                            "reference_strength": "0.6",  # 风格参考强度
                        }

                        response = await client.post(
                            f"{self.api_url}/sdapi/v1/img2img",
                            files=files,
                            data=data,
                        )
                        response.raise_for_status()

                        result = response.json()
                        image_data = result.get("images", [None])[0]
                        if image_data:
                            import base64
                            img_bytes = base64.b64decode(image_data)
                            output_path.write_bytes(img_bytes)
                        else:
                            output_path.write_bytes(response.content)

                        updated_paths.append(str(output_path))
                        logger.info(f"  风格传播完成: {view_name}")

                except httpx.HTTPError as e:
                    logger.warning(f"  风格传播失败 ({Path(other_path).stem}): {e}, 使用原图")
                    updated_paths.append(other_path)

        logger.info(f"风格传播完成, 共 {len(updated_paths)} 个视角")
        return updated_paths


# 全局单例
inpainting_service = InpaintingService()
