"""
阶段四：网格修复 + 导出
POST /api/v1/finalize-and-export
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Form, HTTPException

from app.models.schemas import (
    FinalizeResponse,
    MeshStats,
)
from app.services.mesh_processor import mesh_processor
from app.utils.file_manager import get_session_output_dir, sync_model_to_gallery

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["阶段四：修复与导出"])


@router.post("/finalize-and-export", response_model=FinalizeResponse)
async def finalize_and_export(
    raw_model_path: str = Form(..., description="原始 3D 模型路径"),
    export_format: str = Form(default="stl", description="导出格式: stl / obj"),
    enable_auto_fix: bool = Form(default=True, description="是否启用自动修复"),
    session_id: str = Form(default="", description="会话 ID"),
):
    """
    阶段四：对 3D 模型进行工业级网格修复并导出。

    处理流程：
    1. 加载原始 3D 模型
    2. 网格修复（法线、退化面、重复顶点）
    3. 流形/水密检测
    4. 孔洞填充
    5. 质心计算
    6. 配重腔体生成（防止倾倒）
    7. 重网格化
    8. 导出 STL/OBJ
    9. 返回最终模型路径 + 统计信息
    """
    logger.info(
        f"收到阶段四请求, model={raw_model_path}, "
        f"format={export_format}, auto_fix={enable_auto_fix}"
    )

    # 参数校验
    export_format = export_format.lower().strip(".")
    if export_format not in ("stl", "obj"):
        raise HTTPException(status_code=400, detail="不支持的导出格式，仅支持 stl 和 obj")

    try:
        # 执行完整处理管线
        result = mesh_processor.process_pipeline(
            raw_model_path=raw_model_path,
            export_format=export_format,
            enable_auto_fix=enable_auto_fix,
            session_id=session_id,
        )

        # 同步到 3d-gallery-demo，供 Blender 批处理脚本扫描
        gallery_sync = sync_model_to_gallery(result["final_model_path"], session_id)
        logger.info(f"模型已同步到 3d-gallery-demo: {gallery_sync}")

        return FinalizeResponse(
            session_id=session_id,
            final_model_path=result["final_model_path"],
            mesh_stats=MeshStats(**result["mesh_stats"]),
            center_of_mass=result["center_of_mass"],
            is_manifold=result["is_manifold"],
            holes_fixed=result["holes_fixed"],
            export_format=result["export_format"],
        )

    except Exception as e:
        logger.error(f"阶段四处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"模型修复与导出失败: {str(e)}") from e
