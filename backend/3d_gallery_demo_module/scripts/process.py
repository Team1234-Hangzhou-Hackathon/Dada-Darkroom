#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blender 后台批处理脚本：动态扫描 inputs/ 下所有 .obj / .fbx 模型，统一优化并导出为网页友好的 .glb。

运行方式：
  blender --background --python scripts/process.py

目录约定：
  backend/3d-gallery-demo/
    inputs/   原始 .obj / .fbx
    outputs/  导出的 .glb
    scripts/process.py

设计目标：
  1. 不硬编码模型名称或数量，运行时动态扫描。
  2. 每个模型独立清空场景、导入、减面、重塑 PBR 材质、导出。
  3. 单个模型失败不影响后续模型处理。
"""

from __future__ import annotations

import json
import math
import re
import sys
import traceback
from pathlib import Path
from typing import Iterable, List, Tuple

import mathutils

try:
    import bpy
except ImportError as exc:  # 方便误用普通 python 运行时给出明确提示
    raise RuntimeError(
        "本脚本必须通过 Blender Python 运行，例如："
        "blender --background --python scripts/process.py"
    ) from exc


SUPPORTED_EXTENSIONS = {".obj", ".fbx"}
DECIMATE_RATIO = 0.3
PBR_BASE_COLOR = (0.9, 0.9, 0.9, 1.0)
PBR_METALLIC = 1.0
PBR_ROUGHNESS = 0.15
MANIFEST_FILENAME = "models.json"


def log(message: str) -> None:
    """统一日志输出，并立即刷新，方便在 CI / 终端中观察进度。"""
    print(message, flush=True)


def get_project_root() -> Path:
    """根据脚本所在位置推断模块根目录：backend/3d-gallery-demo。"""
    return Path(__file__).resolve().parents[1]


def ensure_directories(project_root: Path) -> Tuple[Path, Path]:
    """确保 inputs 与 outputs 目录存在。"""
    input_dir = project_root / "inputs"
    output_dir = project_root / "outputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    return input_dir, output_dir


def natural_sort_key(path: Path):
    """自然排序，保证 item2.obj 排在 item10.obj 前面。"""
    text = path.name.lower()
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


def discover_model_files(input_dir: Path) -> List[Path]:
    """动态扫描 inputs 目录下所有支持的模型文件。"""
    if not input_dir.exists():
        return []

    files = [
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files, key=natural_sort_key)


def clear_scene() -> None:
    """彻底清空当前 Blender 场景中的对象、材质、贴图、网格等数据块。"""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # 清理孤立数据，避免批处理多个模型时内存持续膨胀。
    data_collections = (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.textures,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.armatures,
        bpy.data.actions,
    )
    for collection in data_collections:
        for datablock in list(collection):
            if datablock.users == 0:
                collection.remove(datablock)

    # Blender 2.93+ 支持 orphan purge，多执行几次可清理嵌套孤立数据。
    try:
        for _ in range(3):
            bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    except Exception:
        pass


def import_model(model_path: Path) -> List[bpy.types.Object]:
    """根据扩展名导入 OBJ 或 FBX，并返回导入后的对象列表。"""
    before = set(bpy.data.objects)
    suffix = model_path.suffix.lower()

    if suffix == ".obj":
        if hasattr(bpy.ops.wm, "obj_import"):
            bpy.ops.wm.obj_import(filepath=str(model_path))
        else:
            bpy.ops.import_scene.obj(filepath=str(model_path))
    elif suffix == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(model_path))
    else:
        raise ValueError(f"不支持的模型格式: {model_path.suffix}")

    imported = [obj for obj in bpy.data.objects if obj not in before]
    if not imported:
        # 某些导入器不会正确反映 before/after，兜底返回当前场景对象。
        imported = list(bpy.context.scene.objects)

    mesh_objects = [obj for obj in imported if obj.type == "MESH"]
    if not mesh_objects:
        raise RuntimeError(f"导入成功但未发现网格对象: {model_path.name}")

    return imported


def select_objects(objects: Iterable[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    active = None
    scene_objects = bpy.context.scene.objects

    for obj in objects:
        if obj is None:
            continue

        scene_obj = scene_objects.get(obj.name)
        if scene_obj is None:
            continue

        scene_obj.select_set(True)
        if active is None:
            active = scene_obj

    if active is not None:
        bpy.context.view_layer.objects.active = active


def get_mesh_objects() -> List[bpy.types.Object]:
    """获取当前场景中所有网格对象。"""
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def create_industrial_pbr_material() -> bpy.types.Material:
    """创建统一的工业风 PBR 材质。"""
    mat = bpy.data.materials.new(name="Auto_Industrial_PBR")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")

    # 兼容 Blender 3.x / 4.x 的输入名称差异。
    def set_input(names: Tuple[str, ...], value) -> None:
        for name in names:
            socket = bsdf.inputs.get(name)
            if socket is not None:
                socket.default_value = value
                return

    set_input(("Base Color", "BaseColor"), PBR_BASE_COLOR)
    set_input(("Metallic",), PBR_METALLIC)
    set_input(("Roughness",), PBR_ROUGHNESS)

    return mat


def retarget_materials(mesh_objects: Iterable[bpy.types.Object]) -> None:
    """移除原始材质并统一赋予新的 PBR 工业材质。"""
    material = create_industrial_pbr_material()
    for obj in mesh_objects:
        obj.data.materials.clear()
        obj.data.materials.append(material)


def apply_decimate(mesh_objects: Iterable[bpy.types.Object], ratio: float = DECIMATE_RATIO) -> None:
    """为所有网格对象添加并应用 Decimate 修改器。"""
    for obj in mesh_objects:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        modifier = obj.modifiers.new(name="Auto_Decimate_30pct", type="DECIMATE")
        modifier.ratio = ratio
        modifier.use_collapse_triangulate = True

        try:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        except Exception as exc:
            log(f"[Warning] Decimate 应用失败，保留原网格: {obj.name} ({exc})")
        finally:
            obj.select_set(False)


def normalize_scene(mesh_objects: Iterable[bpy.types.Object]) -> None:
    """将模型居中，并按最大尺寸归一化，提升网页展示一致性。"""
    mesh_objects = list(mesh_objects)
    if not mesh_objects:
        return

    select_objects(mesh_objects)

    # 应用导入模型已有的缩放/旋转，避免导出后姿态异常。
    try:
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    except Exception as exc:
        log(f"[Warning] 应用变换失败，继续处理: {exc}")

    bpy.context.view_layer.update()

    min_x = min_y = min_z = math.inf
    max_x = max_y = max_z = -math.inf

    for obj in mesh_objects:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            min_x = min(min_x, world.x)
            min_y = min(min_y, world.y)
            min_z = min(min_z, world.z)
            max_x = max(max_x, world.x)
            max_y = max(max_y, world.y)
            max_z = max(max_z, world.z)

    center = ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, (min_z + max_z) / 2.0)
    max_dim = max(max_x - min_x, max_y - min_y, max_z - min_z)
    scale = 1.0 / max_dim if max_dim > 0 else 1.0

    for obj in mesh_objects:
        obj.location.x = (obj.location.x - center[0]) * scale
        obj.location.y = (obj.location.y - center[1]) * scale
        obj.location.z = (obj.location.z - center[2]) * scale
        obj.scale = (obj.scale.x * scale, obj.scale.y * scale, obj.scale.z * scale)

    select_objects(mesh_objects)
    try:
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
    except Exception as exc:
        log(f"[Warning] 归一化变换应用失败，继续导出: {exc}")


def export_glb(output_path: Path) -> None:
    """导出当前场景选中对象为单文件二进制 GLB。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.export_scene.gltf(
        filepath=str(output_path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_materials="EXPORT",
        export_yup=True,
    )

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"GLB 导出失败或文件为空: {output_path}")


def write_manifest(output_dir: Path) -> None:
    """根据 outputs 目录动态生成 models.json，供后续前端动态菜单使用。"""
    glb_files = sorted(output_dir.glob("*.glb"), key=natural_sort_key)
    models = [
        {
            "name": p.stem,
            "file": p.name,
            "url": f"../outputs/{p.name}",
            "size_bytes": p.stat().st_size,
        }
        for p in glb_files
    ]
    manifest_path = output_dir / MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(models, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"[Manifest] Updated: {manifest_path} ({len(models)} models)")


def process_one(model_path: Path, output_dir: Path) -> Path:
    """处理单个模型文件。"""
    clear_scene()

    imported_objects = import_model(model_path)
    mesh_objects = get_mesh_objects()
    if not mesh_objects:
        raise RuntimeError(f"未发现可处理网格: {model_path.name}")

    retarget_materials(mesh_objects)
    apply_decimate(mesh_objects, DECIMATE_RATIO)

    # Decimate 后重新抓取对象，防止对象引用被 Blender 内部刷新。
    mesh_objects = get_mesh_objects()
    normalize_scene(mesh_objects)

    select_objects(mesh_objects)
    output_path = output_dir / f"{model_path.stem}.glb"
    export_glb(output_path)
    return output_path


def main() -> int:
    project_root = get_project_root()
    input_dir, output_dir = ensure_directories(project_root)

    log("=" * 72)
    log("AI 图生 3D 模型网页化批处理 / Blender Background Pipeline")
    log(f"[Project] {project_root}")
    log(f"[Inputs]  {input_dir}")
    log(f"[Outputs] {output_dir}")
    log(f"[Config]  extensions={sorted(SUPPORTED_EXTENSIONS)}, decimate_ratio={DECIMATE_RATIO}")
    log("=" * 72)

    model_files = discover_model_files(input_dir)
    total = len(model_files)

    if total == 0:
        log("[Info] inputs/ 目录下没有发现 .obj 或 .fbx 文件，无需处理。")
        write_manifest(output_dir)
        return 0

    success_count = 0
    failed: List[Tuple[str, str]] = []

    for index, model_path in enumerate(model_files, start=1):
        try:
            output_path = process_one(model_path, output_dir)
            success_count += 1
            log(f"[Success] {index}/{total} Processed: {model_path.name} -> {output_path.name}")
        except Exception as exc:
            failed.append((model_path.name, str(exc)))
            log(f"[Failed] {index}/{total} Skipped: {model_path.name} ({exc})")
            log(traceback.format_exc())
        finally:
            clear_scene()

    write_manifest(output_dir)

    log("=" * 72)
    log(f"[Done] success={success_count}, failed={len(failed)}, total={total}")
    if failed:
        for name, reason in failed:
            log(f"  - {name}: {reason}")
    log("=" * 72)

    # 存在失败时返回 1，便于自动化流水线感知，但已尽力处理其他文件。
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
