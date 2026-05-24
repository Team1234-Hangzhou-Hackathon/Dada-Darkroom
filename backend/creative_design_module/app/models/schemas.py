"""
Pydantic 请求/响应模型 - 覆盖全部 4 个阶段
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# 阶段一：AI 分析 + 多视角演化
# ──────────────────────────────────────────────
class DesignFeatures(BaseModel):
    """从灵感图像中提取的设计特征"""
    emotion_symbols: list[str] = Field(default_factory=list, description="情感/象征关键词")
    primary_colors: list[str] = Field(default_factory=list, description="主色调列表")
    material_guess: str = Field(default="", description="推测材质")
    style_description: str = Field(default="", description="风格描述")
    structural_keywords: list[str] = Field(default_factory=list, description="结构关键词")


class AnalyzeEvolveResponse(BaseModel):
    """阶段一响应"""
    session_id: str = Field(..., description="会话唯一标识")
    design_features: DesignFeatures
    multi_view_paths: list[str] = Field(default_factory=list, description="5 视角图片路径")
    inspiration_image_path: str = Field(default="", description="灵感原图保存路径")


# ──────────────────────────────────────────────
# 阶段二：人机协同 Inpainting 修改
# ──────────────────────────────────────────────
class ModifyDesignResponse(BaseModel):
    """阶段二响应"""
    session_id: str
    selected_view_index: int
    updated_view_path: str = Field(default="", description="被修改的视角图片路径")
    updated_multi_view_paths: list[str] = Field(default_factory=list, description="更新后的全部视角路径")


# ──────────────────────────────────────────────
# 阶段三：3D 重建 + PBR 纹理
# ──────────────────────────────────────────────
class MaterialSettings(BaseModel):
    """材质参数"""
    material_type: str = Field(default="ceramic", description="材质类型: ceramic/metal/glass/wood/plastic")
    roughness: float = Field(default=0.5, ge=0.0, le=1.0, description="粗糙度 0-1")
    metallic: float = Field(default=0.0, ge=0.0, le=1.0, description="金属度 0-1")
    color_hint: str = Field(default="#FFFFFF", description="颜色提示 HEX")


class Generate3DResponse(BaseModel):
    """阶段三响应"""
    session_id: str
    raw_model_path: str = Field(default="", description="原始 3D 模型路径 (.glb/.obj)")
    texture_paths: dict[str, str] = Field(
        default_factory=dict,
        description="PBR 纹理路径: {albedo, normal, roughness, metallic}",
    )


# ──────────────────────────────────────────────
# 阶段四：网格修复 + 导出
# ──────────────────────────────────────────────
class MeshStats(BaseModel):
    """网格统计信息"""
    vertices: int = Field(default=0, description="顶点数")
    faces: int = Field(default=0, description="面数")
    volume: float = Field(default=0.0, description="体积 (mm³)")
    bounding_box: dict = Field(
        default_factory=dict,
        description="包围盒 {min: [x,y,z], max: [x,y,z], size: [x,y,z]}",
    )


class FinalizeResponse(BaseModel):
    """阶段四响应"""
    session_id: str
    final_model_path: str = Field(default="", description="最终模型文件路径")
    mesh_stats: MeshStats
    center_of_mass: dict = Field(default_factory=dict, description="质心坐标 {x, y, z}")
    is_manifold: bool = Field(default=False, description="是否为流形/水密网格")
    holes_fixed: int = Field(default=0, description="修复的孔洞数量")
    export_format: str = Field(default="stl", description="导出格式")
