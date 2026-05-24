"""
阶段三：3D 重建 + PBR 纹理
POST /api/v1/generate-3d-raw
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Form, HTTPException

from creative_design_module.app.models.schemas import (
    Generate3DResponse,
    MaterialSettings,
)
from creative_design_module.app.services.reconstruction_3d import reconstruction_3d
from creative_design_module.app.services.texture_service import texture_service
from creative_design_module.app.utils.file_manager import get_session_output_dir

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["阶段三：3D 重建"])


@router.post("/generate-3d-raw", response_model=Generate3DResponse)
async def generate_3d_raw(
    multi_view_paths: str = Form(..., description="多视角路径，逗号分隔"),
    material_type: str = Form(default="ceramic", description="材质类型"),
    roughness: float = Form(default=0.5, ge=0.0, le=1.0, description="粗糙度"),
    metallic: float = Form(default=0.0, ge=0.0, le=1.0, description="金属度"),
    color_hint: str = Form(default="#FFFFFF", description="颜色提示"),
    session_id: str = Form(..., description="会话 ID"),
):
    """
    阶段三：从多视角图像生成 3D 模型并添加 PBR 纹理。

    流程：
    1. 解析多视角路径
    2. 调用 TRELLIS 生成 3D 网格
    3. 调用 Meshy 生成 PBR 纹理
    4. 返回模型路径 + 纹理路径
    """
    logger.info(f"收到阶段三请求, session={session_id}")

    # 参数校验
    if not session_id:
        raise HTTPException(status_code=400, detail="缺少会话 ID")

    # 解析多视角路径
    view_paths = [p.strip() for p in multi_view_paths.split(",") if p.strip()]
    if not view_paths:
        raise HTTPException(status_code=400, detail="未提供多视角路径")

    material_settings = MaterialSettings(
        material_type=material_type,
        roughness=roughness,
        metallic=metallic,
        color_hint=color_hint,
    )

    try:
        # 1. 3D 网格重建
        logger.info("开始 3D 网格重建...")
        raw_model_path = await reconstruction_3d.generate_mesh(
            multi_view_paths=view_paths,
            session_id=session_id,
        )
        logger.info(f"3D 网格重建完成: {raw_model_path}")

        # 2. PBR 纹理生成
        logger.info("开始 PBR 纹理生成...")
        texture_paths = await texture_service.generate_pbr_textures(
            mesh_path=raw_model_path,
            material_settings=material_settings,
            session_id=session_id,
        )
        logger.info(f"PBR 纹理生成完成: {list(texture_paths.keys())}")

        return Generate3DResponse(
            session_id=session_id,
            raw_model_path=raw_model_path,
            texture_paths=texture_paths,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"阶段三处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"3D 生成失败: {str(e)}") from e
