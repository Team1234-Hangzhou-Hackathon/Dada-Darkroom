"""
阶段一：AI 分析 + 多视角演化
POST /api/v1/analyze-and-evolve
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models.schemas import AnalyzeEvolveResponse
from app.services.vision_analyzer import vision_analyzer
from app.services.multiview_generator import multiview_generator
from app.utils.file_manager import (
    create_session_dir,
    save_upload_file,
    get_session_upload_dir,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["阶段一：分析与演化"])


@router.post("/analyze-and-evolve", response_model=AnalyzeEvolveResponse)
async def analyze_and_evolve(
    inspiration_image: UploadFile = File(..., description="灵感图像文件"),
):
    """
    阶段一：上传灵感图像，AI 分析设计特征并生成多视角图像。

    流程：
    1. 保存上传的灵感图像
    2. 调用 GPT-4o 进行多模态分析，提取设计特征
    3. 调用 SV3D 生成 5 个标准视角图像
    4. 返回设计特征 + 多视角路径
    """
    logger.info(f"收到阶段一请求, 文件: {inspiration_image.filename}")

    # 校验文件类型
    if not inspiration_image.content_type or not inspiration_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件 (PNG/JPG/JPEG)")

    # 创建会话
    session_id = create_session_dir()
    upload_dir = get_session_upload_dir(session_id)

    try:
        # 1. 保存灵感图像
        image_path = await save_upload_file(
            inspiration_image,
            upload_dir,
            filename="inspiration.png",
        )
        logger.info(f"灵感图像已保存: {image_path}")

        # 2. AI 视觉分析
        design_features = await vision_analyzer.analyze_inspiration(image_path)
        logger.info(f"设计特征提取完成: {design_features.style_description[:50]}...")

        # 3. 多视角生成
        multi_view_paths = await multiview_generator.generate_multi_view(
            image_path=image_path,
            design_features=design_features,
            session_id=session_id,
        )
        logger.info(f"多视角生成完成, 共 {len(multi_view_paths)} 个视角")

        return AnalyzeEvolveResponse(
            session_id=session_id,
            design_features=design_features,
            multi_view_paths=multi_view_paths,
            inspiration_image_path=image_path,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"阶段一处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析与演化失败: {str(e)}") from e
