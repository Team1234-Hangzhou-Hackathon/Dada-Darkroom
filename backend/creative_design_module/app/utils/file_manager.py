"""
文件管理工具 - 处理上传、会话目录、清理等
"""
from __future__ import annotations

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException

from app.config import settings


def _ensure_dir(path: Path) -> Path:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_session_dir() -> str:
    """
    创建一个新的会话目录，返回 session_id。
    目录结构: {UPLOAD_DIR}/{session_id}/
    """
    session_id = uuid.uuid4().hex[:12]
    session_path = _ensure_dir(settings.upload_path / session_id)
    # 同时在 output 目录创建对应目录
    _ensure_dir(settings.output_path / session_id)
    return session_id


def get_session_upload_dir(session_id: str) -> Path:
    """获取会话的上传目录"""
    return settings.upload_path / session_id


def get_session_output_dir(session_id: str) -> Path:
    """获取会话的输出目录"""
    return settings.output_path / session_id


def get_file_path(session_id: str, filename: str, *, output: bool = False) -> str:
    """获取会话中某个文件的完整路径"""
    base = settings.output_path if output else settings.upload_path
    return str(base / session_id / filename)


async def save_upload_file(
    upload_file: UploadFile,
    directory: str | Path,
    filename: Optional[str] = None,
) -> str:
    """
    保存上传文件到指定目录。
    返回保存后的完整文件路径。
    """
    # 校验文件大小
    contents = await upload_file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE // (1024*1024)} MB)",
        )

    # 确定文件名
    if filename is None:
        filename = upload_file.filename or f"{uuid.uuid4().hex[:8]}_upload"

    dir_path = Path(directory)
    _ensure_dir(dir_path)
    file_path = dir_path / filename

    # 写入文件
    with open(file_path, "wb") as f:
        f.write(contents)

    await upload_file.close()
    return str(file_path)


def cleanup_session(session_id: str) -> None:
    """
    清理指定会话的所有文件（上传 + 输出）。
    """
    for base in [settings.upload_path, settings.output_path]:
        session_dir = base / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)


def list_session_files(session_id: str, *, output: bool = False) -> list[str]:
    """列出会话目录中的所有文件"""
    base = settings.output_path if output else settings.upload_path
    session_dir = base / session_id
    if not session_dir.exists():
        return []
    return [str(f) for f in session_dir.iterdir() if f.is_file()]


def sync_model_to_gallery(final_model_path: str, session_id: str) -> dict[str, str]:
    """
    将 creative-design 导出的模型同步到 3d-gallery-demo/inputs。

    3d-gallery-demo/scripts/process.py 会动态扫描 inputs/ 下的 .obj/.fbx，
    因此这里负责把最终模型及其旁路材质文件复制过去。
    """
    src_model = Path(final_model_path)
    if not src_model.exists():
        raise FileNotFoundError(f"最终模型不存在，无法同步到展厅: {final_model_path}")

    # 当前文件位于 backend/creative-design/app/utils/file_manager.py
    # parents[3] => backend
    backend_dir = Path(__file__).resolve().parents[3]
    gallery_input_dir = backend_dir / "3d-gallery-demo" / "inputs"
    gallery_input_dir.mkdir(parents=True, exist_ok=True)

    safe_session = session_id or src_model.parent.name
    dst_model = gallery_input_dir / f"creative_{safe_session}{src_model.suffix.lower()}"
    shutil.copy2(src_model, dst_model)

    copied_assets: list[str] = []
    for asset in src_model.parent.iterdir():
        if asset == src_model:
            continue
        if asset.suffix.lower() in {".mtl", ".png", ".jpg", ".jpeg", ".webp"}:
            dst_asset = gallery_input_dir / asset.name
            shutil.copy2(asset, dst_asset)
            copied_assets.append(str(dst_asset))

    return {
        "gallery_input_model_path": str(dst_model),
        "gallery_input_dir": str(gallery_input_dir),
        "copied_assets": ",".join(copied_assets),
    }
