"""
PBR 纹理生成服务 - 调用 Meshy API 生成物理材质纹理
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings
from app.models.schemas import MaterialSettings

logger = logging.getLogger(__name__)

# PBR 纹理通道
PBR_CHANNELS = ["albedo", "normal", "roughness", "metallic"]


class TextureService:
    """Meshy PBR 纹理生成器"""

    def __init__(self):
        self.api_key = settings.MESHY_API_KEY
        self.base_url = "https://api.meshy.ai/v2"
        self.timeout = httpx.Timeout(300.0, connect=30.0)

    def _get_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def generate_pbr_textures(
        self,
        mesh_path: str,
        material_settings: MaterialSettings,
        session_id: str,
    ) -> dict[str, str]:
        """
        为 3D 网格生成 PBR 纹理贴图。

        Args:
            mesh_path: 3D 模型文件路径
            material_settings: 材质参数
            session_id: 会话 ID

        Returns:
            PBR 纹理路径字典 {albedo, normal, roughness, metallic}
        """
        logger.info(f"开始生成 PBR 纹理, 材质={material_settings.material_type}")

        output_dir = Path(settings.output_path) / session_id / "textures"
        output_dir.mkdir(parents=True, exist_ok=True)

        texture_paths: dict[str, str] = {}

        # 第一步：上传模型到 Meshy
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # 上传模型文件
                with open(mesh_path, "rb") as f:
                    upload_resp = await client.post(
                        f"{self.base_url}/image-to-3d",
                        headers=self._get_headers(),
                        files={"file": ("model.glb", f.read(), "model/gltf-binary")},
                        data={
                            "material_type": material_settings.material_type,
                            "roughness": str(material_settings.roughness),
                            "metallic": str(material_settings.metallic),
                            "color_hint": material_settings.color_hint,
                        },
                    )
                upload_resp.raise_for_status()
                task_data = upload_resp.json()
                task_id = task_data.get("result", "")

                if not task_id:
                    raise RuntimeError(f"Meshy 上传失败: {task_data}")

                logger.info(f"Meshy 任务已创建: {task_id}")

                # 第二步：轮询等待纹理生成完成
                import asyncio
                for attempt in range(60):  # 最多等待 5 分钟
                    await asyncio.sleep(5)
                    status_resp = await client.get(
                        f"{self.base_url}/image-to-3d/{task_id}",
                        headers=self._get_headers(),
                    )
                    status_resp.raise_for_status()
                    status_data = status_resp.json()
                    status = status_data.get("status", "")

                    if status == "SUCCEEDED":
                        # 下载纹理贴图
                        texture_urls = status_data.get("texture_urls", {})
                        for channel in PBR_CHANNELS:
                            url = texture_urls.get(channel, "")
                            if url:
                                tex_resp = await client.get(url)
                                tex_resp.raise_for_status()
                                tex_path = output_dir / f"{channel}.png"
                                tex_path.write_bytes(tex_resp.content)
                                texture_paths[channel] = str(tex_path)

                        logger.info(f"PBR 纹理生成完成: {list(texture_paths.keys())}")
                        return texture_paths

                    elif status == "FAILED":
                        raise RuntimeError(f"Meshy 纹理生成失败: {status_data}")

                    logger.debug(f"  Meshy 任务状态: {status} (尝试 {attempt + 1}/60)")

                raise RuntimeError("Meshy 纹理生成超时")

            except httpx.HTTPError as e:
                logger.error(f"Meshy API 调用失败: {e}")
                raise RuntimeError(f"PBR 纹理生成服务调用失败: {e}") from e


# 全局单例
texture_service = TextureService()
