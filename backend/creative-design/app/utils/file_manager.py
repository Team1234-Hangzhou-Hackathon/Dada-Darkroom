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
