"""
3D 重建服务 - 使用 Meshy Multi-Image to 3D 从多视角图直接生成带纹理的 GLB。

说明：
- 直接使用多视角图像，不再走 Text-to-3D 文本提示。
- 开启 should_texture + enable_pbr，尽量保证输出带颜色/贴图。
- Meshy 是异步任务模型：先创建任务，再轮询，最后下载 GLB。
"""
from __future__ import annotations

import asyncio
import base64
import logging
import mimetypes
from pathlib import Path

import httpx

from creative_design_module.app.config import settings

logger = logging.getLogger(__name__)


class Reconstruction3D:
    """Meshy 多视角 3D 重建器"""

    def __init__(self):
        self.api_key = settings.MESHY_API_KEY
        self.base_url = "https://api.meshy.ai"
        self.timeout = httpx.Timeout(600.0, connect=30.0)

    def _get_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _to_data_uri(self, image_path: str) -> str:
        """把本地图片转成 Meshy 可接收的 base64 data URI。"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"多视角图片不存在: {image_path}")

        mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
        data = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f"data:{mime_type};base64,{data}"

    def _select_views(self, multi_view_paths: list[str]) -> list[str]:
        """Meshy multi-image-to-3d 最多支持 4 张图，优先使用前 4 张。"""
        if not multi_view_paths:
            raise ValueError("缺少多视角图片，无法调用 Meshy multi-image-to-3d")
        return multi_view_paths[:4]

    async def generate_mesh(
        self,
        multi_view_paths: list[str],
        session_id: str,
    ) -> str:
        """
        使用 Meshy Multi-Image to 3D 生成带纹理的 3D 模型。
        """
        logger.info(f"开始 Meshy Multi-Image to 3D 重建, 视角数={len(multi_view_paths)}, session={session_id}")

        if not self.api_key:
            raise RuntimeError("未配置 MESHY_API_KEY")

        output_dir = Path(settings.output_path) / session_id / "3d_model"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "raw_model.glb"

        selected_views = self._select_views(multi_view_paths)
        image_urls = [self._to_data_uri(p) for p in selected_views]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                task_id = await self._create_task(client, image_urls)
                task = await self._poll_task(client, task_id)
                model_url = task.get("model_urls", {}).get("glb")
                if not model_url:
                    raise RuntimeError(f"Meshy 任务完成但未返回 GLB 链接: {task}")

                download_resp = await client.get(model_url)
                download_resp.raise_for_status()
                output_path.write_bytes(download_resp.content)
                logger.info(f"Meshy Multi-Image to 3D 完成: {output_path}")
                return str(output_path)
            except httpx.HTTPError as e:
                logger.error(f"Meshy API 调用失败: {e}")
                raise RuntimeError(f"3D 重建服务调用失败: {e}") from e

    async def _create_task(self, client: httpx.AsyncClient, image_urls: list[str]) -> str:
        payload = {
            "image_urls": image_urls,
            "ai_model": "latest",
            "should_texture": True,
            "enable_pbr": True,
            "hd_texture": False,
            "should_remesh": True,
            "target_formats": ["glb"],
            "image_enhancement": True,
            "remove_lighting": True,
            "moderation": False,
            "auto_size": False,
        }
        response = await client.post(
            f"{self.base_url}/openapi/v1/multi-image-to-3d",
            headers=self._get_headers(),
            json=payload,
        )
        response.raise_for_status()
        task_id = response.json().get("result", "")
        if not task_id:
            raise RuntimeError(f"Meshy multi-image 任务创建失败: {response.text}")
        logger.info(f"Meshy multi-image 任务已创建: {task_id}")
        return task_id

    async def _poll_task(self, client: httpx.AsyncClient, task_id: str) -> dict:
        last_status = ""
        for _ in range(240):  # 最多 20 分钟
            await asyncio.sleep(5)
            response = await client.get(
                f"{self.base_url}/openapi/v1/multi-image-to-3d/{task_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            task = response.json()
            status = task.get("status", "")
            progress = task.get("progress", 0)
            if status != last_status:
                logger.info(f"Meshy 任务状态: {status} | progress={progress} | task={task_id}")
                last_status = status
            if status == "SUCCEEDED":
                return task
            if status in {"FAILED", "CANCELED"}:
                raise RuntimeError(f"Meshy 任务失败: {task}")
        raise RuntimeError(f"Meshy 任务轮询超时: {task_id}")

    async def check_status(self, task_id: str) -> dict:
        """查询异步重建任务状态"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/openapi/v1/multi-image-to-3d/{task_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()


# 全局单例
reconstruction_3d = Reconstruction3D()
