"""
3D 重建服务 - 调用 TRELLIS API 从多视角图像生成 3D 网格
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class Reconstruction3D:
    """TRELLIS / Hunyuan3D 3D 网格重建器"""

    def __init__(self):
        self.api_url = settings.TRELLIS_API_URL.rstrip("/")
        self.timeout = httpx.Timeout(600.0, connect=30.0)  # 3D 重建可能需要较长时间

    async def generate_mesh(
        self,
        multi_view_paths: list[str],
        session_id: str,
    ) -> str:
        """
        从多视角图像生成 3D 网格模型。

        Args:
            multi_view_paths: 多视角图像路径列表
            session_id: 会话 ID

        Returns:
            生成的 3D 模型文件路径 (.glb)
        """
        logger.info(f"开始 3D 重建, 视角数={len(multi_view_paths)}, session={session_id}")

        output_dir = Path(settings.output_path) / session_id / "3d_model"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "raw_model.glb"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 构建多文件上传
            files = []
            for i, view_path in enumerate(multi_view_paths):
                with open(view_path, "rb") as f:
                    files.append(
                        ("images", (f"view_{i}.png", f.read(), "image/png"))
                    )

            data = {
                "output_format": "glb",
                "texture_resolution": "1024",
                "geometry_quality": "high",
            }

            try:
                response = await client.post(
                    f"{self.api_url}/reconstruct",
                    files=files,
                    data=data,
                )
                response.raise_for_status()

                # 保存模型文件
                result = response.json()
                model_url = result.get("model_url", "")
                if model_url:
                    # 如果 API 返回下载链接
                    download_resp = await client.get(model_url)
                    download_resp.raise_for_status()
                    output_path.write_bytes(download_resp.content)
                else:
                    # 如果直接返回二进制
                    output_path.write_bytes(response.content)

                logger.info(f"3D 重建完成: {output_path}")
                return str(output_path)

            except httpx.HTTPError as e:
                logger.error(f"3D 重建 API 调用失败: {e}")
                raise RuntimeError(f"3D 重建服务调用失败: {e}") from e

    async def check_status(self, task_id: str) -> dict:
        """查询异步重建任务状态"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.api_url}/status/{task_id}")
            response.raise_for_status()
            return response.json()


# 全局单例
reconstruction_3d = Reconstruction3D()
