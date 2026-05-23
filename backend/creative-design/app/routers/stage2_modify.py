"""
阶段二：人机协同 Inpainting 修改
POST /api/v1/modify-design
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.models.schemas import ModifyDesignResponse
from app.services.inpainting_service import inpainting_service
from app.utils.file_manager import (
    save_upload_file,
    get_session_upload_dir,
    get_session_output_dir,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["阶段二：设计修改"])


@router.post("/modify-design", response_model=ModifyDesignResponse)
async def modify_design(
    selected_view_index: int = Form(..., description="选择的视角索引 (0-4)"),
    mask_image: UploadFile = File(..., description="蒙版图像（白色区域为重绘区域）"),
    prompt_text: str = Form(..., description="修改提示词"),
    session_id: str = Form(..., description="会话 ID"),
):
    """
    阶段二：人机协同修改设计。

    流程：
    1. 用户选择一个视角并上传蒙版
    2. 使用 Stable Diffusion Inpainting 对选中视角进行修改
    3. 将修改传播到其他视角以保持一致性
    4. 返回更新后的所有视角路径
    """
    logger.info(
        f"收到阶段二请求, session={session_id}, "
        f"view_index={selected_view_index}, prompt={prompt_text[:50]}"
    )

    # 参数校验
    if selected_view_index < 0 or selected_view_index > 4:
        raise HTTPException(status_code=400, detail="视角索引必须在 0-4 之间")

    if not session_id:
        raise HTTPException(status_code=400, detail="缺少会话 ID")

    output_dir = get_session_output_dir(session_id)

    try:
        # 1. 保存蒙版图像
        mask_path = await save_upload_file(
            mask_image,
            output_dir,
            filename="mask.png",
        )

        # 2. 获取选中视角的路径
        multi_view_dir = output_dir / "multi_views"
        view_names = ["view_front.png", "view_back.png", "view_left.png", "view_right.png", "view_top.png"]
        selected_view_path = str(multi_view_dir / view_names[selected_view_index])

        if not multi_view_dir.exists():
            raise HTTPException(
                status_code=404,
                detail="未找到多视角图像，请先完成阶段一",
            )

        # 3. 执行 inpainting
        updated_view_path = await inpainting_service.inpaint_view(
            view_path=selected_view_path,
            mask_path=mask_path,
            prompt=prompt_text,
            session_id=session_id,
        )

        # 4. 收集其他视角路径
        other_view_paths = []
        for i, name in enumerate(view_names):
            if i != selected_view_index:
                path = multi_view_dir / name
                if path.exists():
                    other_view_paths.append(str(path))

        # 5. 风格传播
        updated_multi_view_paths = await inpainting_service.propagate_changes(
            modified_view_path=updated_view_path,
            other_view_paths=other_view_paths,
            prompt=prompt_text,
            session_id=session_id,
        )

        return ModifyDesignResponse(
            session_id=session_id,
            selected_view_index=selected_view_index,
            updated_view_path=updated_view_path,
            updated_multi_view_paths=updated_multi_view_paths,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"阶段二处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"设计修改失败: {str(e)}") from e
