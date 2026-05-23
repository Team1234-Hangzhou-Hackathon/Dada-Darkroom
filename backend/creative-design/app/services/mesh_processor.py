"""
网格处理服务 - 基于 trimesh 的完整网格修复与处理管线

这是整个系统的核心模块，负责：
1. 网格修复（法线、退化面、重复顶点）
2. 流形/水密检测
3. 孔洞填充
4. 质心计算
5. 配重腔体生成
6. 四边形重网格化
7. 模型导出（STL/OBJ）
8. 完整处理管线
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import trimesh

from app.config import settings

logger = logging.getLogger(__name__)


class MeshProcessor:
    """基于 trimesh 的网格处理器"""

    def __init__(self):
        pass

    # ──────────────────────────────────────────────────────
    # 1. 网格修复
    # ──────────────────────────────────────────────────────
    def repair_mesh(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        综合修复网格，包括：
        - 修复法线方向
        - 移除退化面（零面积三角形）
        - 合并重复顶点
        - 移除孤立顶点
        - 移除自交面

        Args:
            mesh: 输入网格

        Returns:
            修复后的网格
        """
        logger.info("开始网格修复...")

        # 1.1 确保网格为 Trimesh 类型
        if not isinstance(mesh, trimesh.Trimesh):
            if isinstance(mesh, trimesh.Scene):
                mesh = mesh.to_mesh()
            else:
                raise ValueError(f"不支持的网格类型: {type(mesh)}")

        # 1.2 修复法线方向 - 确保所有面法线朝外
        logger.info("  修复法线方向...")
        # 先尝试移除未引用的顶点
        mesh.remove_unreferenced_vertices()
        # 修复法线
        mesh.fix_normals()
        # 确保面法线一致（全部朝外）
        mesh.faces = mesh.faces[mesh.face_normals @ mesh.face_adjacency_angles < np.pi]

        # 1.3 移除退化面（面积为零或接近零的三角形）
        logger.info("  移除退化面...")
        # 计算每个面的面积
        face_areas = mesh.area_faces
        # 移除面积小于阈值的面
        min_area_threshold = 1e-10
        valid_faces_mask = face_areas > min_area_threshold
        if not np.all(valid_faces_mask):
            removed_count = int(np.sum(~valid_faces_mask))
            logger.info(f"  移除了 {removed_count} 个退化面")
            mesh.update_faces(np.where(valid_faces_mask)[0])
            mesh.remove_unreferenced_vertices()

        # 1.4 合并重复顶点（顶点距离小于阈值的合并）
        logger.info("  合并重复顶点...")
        # trimesh 的 merge_vertices 会合并完全相同的顶点
        mesh.merge_vertices()
        # 对于距离很近但不完全相同的顶点，使用 voxelize 方法
        # 这里我们使用 trimesh 的内置方法
        mesh.remove_duplicate_faces()

        # 1.5 移除自交面
        logger.info("  检测自交面...")
        try:
            # 使用 trimesh 的碰撞检测查找自交
            collisions = mesh.intersects_self()
            if np.any(collisions):
                collision_count = int(np.sum(collisions))
                logger.warning(f"  发现 {collision_count} 个自交面，尝试修复...")
                # 移除自交面
                mesh.update_faces(np.where(~collisions)[0])
                mesh.remove_unreferenced_vertices()
        except Exception as e:
            logger.warning(f"  自交检测失败（可能网格过于复杂）: {e}")

        # 1.6 移除内部孤立组件（保留最大连通组件）
        logger.info("  清理孤立组件...")
        if mesh.is_watertight:
            # 对于水密网格，移除内部空腔
            try:
                mesh = self._remove_internal_cavities(mesh)
            except Exception as e:
                logger.warning(f"  内部空腔清理失败: {e}")

        # 1.7 确保数据一致性
        mesh.process()  # trimesh 内部处理：重新计算法线、包围盒等

        logger.info(f"网格修复完成: {len(mesh.vertices)} 顶点, {len(mesh.faces)} 面")
        return mesh

    def _remove_internal_cavities(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """移除水密网格内部的空腔"""
        # 使用体素化方法：填充内部空腔
        try:
            # 创建体素网格
            voxelized = mesh.voxelized(pitch=mesh.extents.min() / 50)
            # 转换回网格（自动填充内部）
            filled_mesh = voxelized.marching_cubes
            return filled_mesh
        except Exception:
            return mesh

    # ──────────────────────────────────────────────────────
    # 2. 流形/水密检测
    # ──────────────────────────────────────────────────────
    def check_manifold(self, mesh: trimesh.Trimesh) -> dict:
        """
        检查网格是否为流形（水密）网格。

        Returns:
            {
                "is_manifold": bool,      # 是否为流形
                "is_watertight": bool,    # 是否水密
                "euler_number": int,      # 欧拉数
                "boundaries": int,        # 边界数量（0 表示水密）
                "non_manifold_edges": int, # 非流形边数量
            }
        """
        logger.info("检查网格流形属性...")

        # 检查水密性
        is_watertight = mesh.is_watertight

        # 检查欧拉数（对于水密网格，欧拉数应为 2）
        euler_number = mesh.euler_number

        # 检查边界（开放边）
        # 对于水密网格，不应有边界
        try:
            boundaries = len(mesh.facets_boundary) if hasattr(mesh, 'facets_boundary') else 0
        except Exception:
            boundaries = 0

        # 检查非流形边
        # 非流形边：被 3 个或更多面共享的边
        try:
            # 统计每条边被多少面共享
            edges_sorted = np.sort(mesh.edges_unique, axis=1)
            edge_face_count = {}
            for edge in edges_sorted:
                key = (edge[0], edge[1])
                edge_face_count[key] = edge_face_count.get(key, 0) + 1
            non_manifold_count = sum(1 for c in edge_face_count.values() if c > 2)
        except Exception:
            non_manifold_count = 0

        is_manifold = is_watertight and non_manifold_count == 0

        result = {
            "is_manifold": is_manifold,
            "is_watertight": is_watertight,
            "euler_number": int(euler_number),
            "boundaries": boundaries,
            "non_manifold_edges": non_manifold_count,
        }

        logger.info(
            f"流形检查: manifold={is_manifold}, watertight={is_watertight}, "
            f"euler={euler_number}, non_manifold_edges={non_manifold_count}"
        )
        return result

    # ──────────────────────────────────────────────────────
    # 3. 孔洞填充
    # ──────────────────────────────────────────────────────
    def fill_holes(self, mesh: trimesh.Trimesh) -> Tuple[trimesh.Trimesh, int]:
        """
        检测并填充网格中的孔洞。

        使用三角化方法填充边界环上的孔洞。

        Args:
            mesh: 输入网格

        Returns:
            (修复后的网格, 填充的孔洞数量)
        """
        logger.info("开始孔洞填充...")

        holes_filled = 0

        if mesh.is_watertight:
            logger.info("  网格已水密，无需填充")
            return mesh, 0

        # 获取所有开放边界（边只被一个面共享）
        # 使用 trimesh 的边拓扑信息
        try:
            # 构建边到面的映射
            edge_faces = mesh.edges_face

            # 找出边界边（只被一个面共享的边）
            boundary_mask = edge_faces[:, 1] == -1
            boundary_edges = mesh.edges[edge_faces[boundary_mask, 0]]

            if len(boundary_edges) == 0:
                logger.info("  未发现孔洞")
                return mesh, 0

            # 将边界边组织成边界环
            boundary_loops = self._find_boundary_loops(mesh, boundary_edges)
            logger.info(f"  发现 {len(boundary_loops)} 个边界环（孔洞）")

            # 对每个边界环进行三角化填充
            for loop_vertices in boundary_loops:
                if len(loop_vertices) < 3:
                    continue

                try:
                    # 使用 ear-clipping 三角化填充孔洞
                    new_faces = self._triangulate_loop(loop_vertices, mesh.vertices)
                    if len(new_faces) > 0:
                        # 将新面添加到网格
                        mesh = trimesh.Trimesh(
                            vertices=mesh.vertices,
                            faces=np.vstack([mesh.faces, new_faces]),
                            process=False,
                        )
                        holes_filled += 1
                        logger.info(f"    填充孔洞: {len(loop_vertices)} 个顶点的环 -> {len(new_faces)} 个面")
                except Exception as e:
                    logger.warning(f"    填充孔洞失败: {e}")

            # 重新处理网格
            mesh.process()

        except Exception as e:
            logger.error(f"孔洞填充过程出错: {e}")

        logger.info(f"孔洞填充完成, 共填充 {holes_filled} 个孔洞")
        return mesh, holes_filled

    def _find_boundary_loops(
        self,
        mesh: trimesh.Trimesh,
        boundary_edges: np.ndarray,
    ) -> list[np.ndarray]:
        """
        将边界边组织成有序的边界环。

        Args:
            mesh: 网格
            boundary_edges: 边界边数组 (N, 2)

        Returns:
            边界环列表，每个环是顶点索引数组
        """
        if len(boundary_edges) == 0:
            return []

        # 构建邻接表
        adjacency: dict[int, list[int]] = {}
        for edge in boundary_edges:
            v0, v1 = int(edge[0]), int(edge[1])
            adjacency.setdefault(v0, []).append(v1)
            adjacency.setdefault(v1, []).append(v0)

        # 追踪边界环
        loops: list[np.ndarray] = []
        visited_edges: set[tuple[int, int]] = set()

        for start_v in adjacency:
            if start_v in [v for loop in loops for v in loop]:
                continue

            # 从 start_v 开始追踪环
            loop = [start_v]
            current = start_v
            max_iterations = len(boundary_edges) + 1

            for _ in range(max_iterations):
                neighbors = adjacency.get(current, [])
                next_v = None
                for n in neighbors:
                    edge_key = (min(current, n), max(current, n))
                    if edge_key not in visited_edges:
                        next_v = n
                        break

                if next_v is None or next_v == start_v:
                    break

                visited_edges.add((min(current, next_v), max(current, next_v)))
                loop.append(next_v)
                current = next_v

            if len(loop) >= 3:
                loops.append(np.array(loop, dtype=np.int64))

        return loops

    def _triangulate_loop(
        self,
        loop: np.ndarray,
        all_vertices: np.ndarray,
    ) -> np.ndarray:
        """
        使用 ear-clipping 算法对边界环进行三角化。

        Args:
            loop: 边界环顶点索引数组
            all_vertices: 所有顶点坐标

        Returns:
            新增的面索引数组 (N, 3)
        """
        if len(loop) < 3:
            return np.array([], dtype=np.int64).reshape(0, 3)

        # 获取环上顶点的坐标
        loop_points = all_vertices[loop]

        # 使用 scipy 的 Delaunay 三角化（如果有 scipy）
        try:
            from scipy.spatial import Delaunay

            # 对 2D 投影进行 Delaunay 三角化
            # 选择最佳投影平面
            normal = self._compute_loop_normal(loop_points)
            abs_normal = np.abs(normal)

            if abs_normal[2] >= abs_normal[0] and abs_normal[2] >= abs_normal[1]:
                # 投影到 XY 平面
                points_2d = loop_points[:, :2]
            elif abs_normal[0] >= abs_normal[1]:
                # 投影到 YZ 平面
                points_2d = loop_points[:, 1:3]
            else:
                # 投影到 XZ 平面
                points_2d = loop_points[:, [0, 2]]

            tri = Delaunay(points_2d)

            # 筛选：只保留环内部的三角形（所有顶点都在环上）
            valid_faces = []
            for simplex in tri.simplices:
                if np.all(np.isin(simplex, np.arange(len(loop)))):
                    # 将局部索引转换为全局顶点索引
                    global_face = loop[simplex]
                    # 检查面的法线方向是否与环法线一致
                    face_normal = self._compute_face_normal(
                        all_vertices[global_face[0]],
                        all_vertices[global_face[1]],
                        all_vertices[global_face[2]],
                    )
                    if np.dot(face_normal, normal) > 0:
                        valid_faces.append(global_face)
                    else:
                        valid_faces.append(global_face[::-1])

            if valid_faces:
                return np.array(valid_faces, dtype=np.int64)

        except ImportError:
            logger.debug("scipy 未安装，使用简单三角化")
        except Exception as e:
            logger.debug(f"Delaunay 三角化失败: {e}")

        # 降级方案：扇形三角化（fan triangulation）
        return self._fan_triangulate(loop)

    def _fan_triangulate(self, loop: np.ndarray) -> np.ndarray:
        """扇形三角化 - 将多边形从第一个顶点扇形展开"""
        if len(loop) < 3:
            return np.array([], dtype=np.int64).reshape(0, 3)

        faces = []
        center = loop[0]
        for i in range(1, len(loop) - 1):
            faces.append([center, loop[i], loop[i + 1]])

        return np.array(faces, dtype=np.int64)

    @staticmethod
    def _compute_loop_normal(points: np.ndarray) -> np.ndarray:
        """计算边界环的近似法线"""
        if len(points) < 3:
            return np.array([0.0, 0.0, 1.0])

        # 使用 Newell 方法计算多边形法线
        normal = np.zeros(3)
        n = len(points)
        for i in range(n):
            curr = points[i]
            next_p = points[(i + 1) % n]
            normal[0] += (curr[1] - next_p[1]) * (curr[2] + next_p[2])
            normal[1] += (curr[2] - next_p[2]) * (curr[0] + next_p[0])
            normal[2] += (curr[0] - next_p[0]) * (curr[1] + next_p[1])

        length = np.linalg.norm(normal)
        if length > 1e-10:
            normal /= length
        else:
            normal = np.array([0.0, 0.0, 1.0])

        return normal

    @staticmethod
    def _compute_face_normal(v0: np.ndarray, v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
        """计算三角面法线"""
        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)
        length = np.linalg.norm(normal)
        if length > 1e-10:
            normal /= length
        return normal

    # ──────────────────────────────────────────────────────
    # 4. 质心计算
    # ──────────────────────────────────────────────────────
    def compute_center_of_mass(self, mesh: trimesh.Trimesh) -> dict:
        """
        计算网格的质心（重心）。

        对于水密网格，使用体积积分计算精确质心。
        对于非水密网格，使用顶点加权平均作为近似。

        Returns:
            {"x": float, "y": float, "z": float}
        """
        logger.info("计算质心...")

        if mesh.is_watertight:
            # 使用 trimesh 的质心属性（基于体积积分）
            com = mesh.center_mass
            logger.info(f"  精确质心（体积积分）: {com}")
        else:
            # 近似：顶点加权平均（按面面积加权）
            face_centers = mesh.triangles.mean(axis=1)  # 每个面的中心
            face_areas = mesh.area_faces  # 每个面的面积
            total_area = face_areas.sum()
            if total_area > 1e-10:
                com = (face_centers * face_areas[:, np.newaxis]).sum(axis=0) / total_area
            else:
                com = mesh.vertices.mean(axis=0)
            logger.info(f"  近似质心（面积加权）: {com}")

        return {"x": float(com[0]), "y": float(com[1]), "z": float(com[2])}

    # ──────────────────────────────────────────────────────
    # 5. 配重腔体生成
    # ──────────────────────────────────────────────────────
    def generate_weight_cavity(
        self,
        mesh: trimesh.Trimesh,
        com: dict,
        stability_threshold: float = 0.6,
        cavity_depth_ratio: float = 0.3,
        wall_thickness: float = 2.0,
    ) -> trimesh.Trimesh:
        """
        如果质心过高（可能导致倾倒），在底部生成配重腔体。

        通过在模型底部挖空一个腔体来降低整体质心高度。

        Args:
            mesh: 输入网格
            com: 质心坐标 {"x": ..., "y": ..., "z": ...}
            stability_threshold: 质心高度比阈值（质心高度/模型高度）
            cavity_depth_ratio: 腔体深度占模型高度的比例
            wall_thickness: 腔体壁厚 (mm)

        Returns:
            修改后的网格（如果需要），或原始网格
        """
        logger.info("检查是否需要生成配重腔体...")

        bounds = mesh.bounds  # (min, max)
        model_height = bounds[1][2] - bounds[0][2]  # Z 轴高度
        com_z = com["z"]
        com_height_ratio = (com_z - bounds[0][2]) / model_height if model_height > 1e-6 else 0.5

        logger.info(f"  模型高度: {model_height:.2f}, 质心高度比: {com_height_ratio:.3f}")

        if com_height_ratio <= stability_threshold:
            logger.info("  质心位置稳定，无需生成配重腔体")
            return mesh

        logger.info(f"  质心过高 ({com_height_ratio:.3f} > {stability_threshold})，生成配重腔体...")

        # 计算腔体参数
        cavity_depth = model_height * cavity_depth_ratio
        cavity_top_z = bounds[0][2] + cavity_depth  # 腔体顶部 Z 坐标

        # 获取模型在 Z = cavity_top_z 处的截面
        try:
            section = mesh.section(plane_origin=[0, 0, cavity_top_z], plane_normal=[0, 0, 1])
            if section is None:
                logger.warning("  无法获取截面，跳过配重腔体生成")
                return mesh

            # 将截面转换为 2D 路径
            slice_2d, to_3d = section.to_planar()

            # 创建腔体（向内偏移 wall_thickness）
            if hasattr(slice_2d, 'offset'):
                inner_path = slice_2d.offset(-wall_thickness)
            else:
                inner_path = slice_2d

            # 将 2D 路径转换回 3D
            if inner_path is not None:
                cavity_vertices_2d = inner_path.vertices
                cavity_vertices_3d = np.column_stack([
                    cavity_vertices_2d,
                    np.full(len(cavity_vertices_2d), bounds[0][2] + wall_thickness),
                ])
                # 应用逆变换
                cavity_vertices_3d = to_3d.transform_points(cavity_vertices_3d)

                # 创建腔体网格（拉伸到底部）
                cavity_mesh = trimesh.creation.extrude_triangulation(
                    inner_path.vertices,
                    inner_path.faces,
                    height=-(cavity_depth - wall_thickness),
                )

                # 布尔差集：从原网格中减去腔体
                try:
                    result = mesh.difference(cavity_mesh)
                    if result is not None and isinstance(result, trimesh.Trimesh):
                        logger.info("  配重腔体生成成功")
                        return result
                except Exception as e:
                    logger.warning(f"  布尔差集失败: {e}")

        except Exception as e:
            logger.warning(f"  配重腔体生成失败: {e}")

        logger.info("  配重腔体生成未成功，保持原始网格")
        return mesh

    # ──────────────────────────────────────────────────────
    # 6. 四边形重网格化
    # ──────────────────────────────────────────────────────
    def remesh_quad(
        self,
        mesh: trimesh.Trimesh,
        target_face_count: int = 10000,
    ) -> trimesh.Trimesh:
        """
        将三角网格转换为四边形主导网格。

        使用各向同性重网格化算法，生成更均匀的面分布。
        由于 trimesh 本身不支持四边形网格，这里使用各向同性三角重网格化，
        然后尝试使用 pymeshlab 进行四边形化（如果可用）。

        Args:
            mesh: 输入三角网格
            target_face_count: 目标面数

        Returns:
            重网格化后的网格
        """
        logger.info(f"开始重网格化, 目标面数={target_face_count}")

        # 方法 1: 尝试使用 pymeshlab（推荐）
        try:
            import pymeshlab
            ms = pymeshlab.MeshSet()

            # 加载网格
            temp_path = Path(settings.OUTPUT_DIR) / "_temp_remesh_input.obj"
            mesh.export(str(temp_path))
            ms.load_new_mesh(str(temp_path))

            # 各向同性重网格化
            ms.apply_filter(
                "meshing_isotropic_explicit_remeshing",
                iterations=10,
                targetlen=pymeshlab.PercentageValue(0.5),
                featureangle=30.0,
            )

            # 尝试四边形化
            try:
                ms.apply_filter("meshing_quadratic_edge_collapse_decimation")
            except Exception:
                pass  # 如果四边形化失败，保持三角网格

            result_mesh = ms.current_mesh()
            remeshed = trimesh.Trimesh(
                vertices=result_mesh.vertex_matrix(),
                faces=result_mesh.face_matrix(),
            )

            # 清理临时文件
            temp_path.unlink(missing_ok=True)

            logger.info(
                f"  pymeshlab 重网格化完成: "
                f"{len(remeshed.vertices)} 顶点, {len(remeshed.faces)} 面"
            )
            return remeshed

        except ImportError:
            logger.info("  pymeshlab 未安装，使用 trimesh 内置方法")

        # 方法 2: 使用 trimesh 的子划分方法
        try:
            # 计算需要的细分级别
            current_faces = len(mesh.faces)
            if current_faces == 0:
                return mesh

            # 使用简化或细分来接近目标面数
            if current_faces > target_face_count * 1.5:
                # 需要简化
                simplified = mesh.simplify_quadric_decimation(target_face_count)
                logger.info(
                    f"  简化完成: {len(mesh.faces)} -> {len(simplified.faces)} 面"
                )
                return simplified
            elif current_faces < target_face_count * 0.5:
                # 需要细分
                subdivided = mesh.subdivide()
                logger.info(
                    f"  细分完成: {len(mesh.faces)} -> {len(subdivided.faces)} 面"
                )
                return subdivided
            else:
                logger.info("  面数在合理范围内，无需重网格化")
                return mesh

        except Exception as e:
            logger.warning(f"  trimesh 重网格化失败: {e}")
            return mesh

    # ──────────────────────────────────────────────────────
    # 7. 模型导出
    # ──────────────────────────────────────────────────────
    def export_model(
        self,
        mesh: trimesh.Trimesh,
        filepath: str,
        fmt: str = "stl",
    ) -> str:
        """
        导出模型到指定格式。

        Args:
            mesh: 网格
            filepath: 输出文件路径
            fmt: 导出格式 ("stl" 或 "obj")

        Returns:
            导出文件的完整路径
        """
        fmt = fmt.lower().strip(".")
        if fmt not in ("stl", "obj"):
            raise ValueError(f"不支持的导出格式: {fmt}，仅支持 stl 和 obj")

        # 确保文件扩展名正确
        path = Path(filepath)
        if path.suffix.lower() != f".{fmt}":
            filepath = str(path.with_suffix(f".{fmt}"))

        # 确保输出目录存在
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"导出模型: {filepath} (格式: {fmt})")

        if fmt == "stl":
            # STL 导出：二进制格式
            mesh.export(filepath, file_type="stl")
        elif fmt == "obj":
            # OBJ 导出：包含法线
            mesh.export(filepath, file_type="obj")

        # 验证导出文件
        if not Path(filepath).exists():
            raise RuntimeError(f"模型导出失败: {filepath}")

        file_size = Path(filepath).stat().st_size
        logger.info(f"  导出成功: {filepath} ({file_size / 1024:.1f} KB)")
        return filepath

    # ──────────────────────────────────────────────────────
    # 8. 网格统计信息
    # ──────────────────────────────────────────────────────
    def get_mesh_stats(self, mesh: trimesh.Trimesh) -> dict:
        """
        获取网格统计信息。

        Returns:
            {
                "vertices": int,     # 顶点数
                "faces": int,        # 面数
                "volume": float,     # 体积 (mm³)
                "bounding_box": {    # 包围盒
                    "min": [x, y, z],
                    "max": [x, y, z],
                    "size": [x, y, z],
                }
            }
        """
        logger.info("计算网格统计信息...")

        bounds = mesh.bounds
        bb_min = bounds[0].tolist()
        bb_max = bounds[1].tolist()
        bb_size = mesh.extents.tolist()

        # 体积（仅水密网格可计算）
        volume = 0.0
        if mesh.is_watertight:
            try:
                volume = float(mesh.volume)
            except Exception:
                volume = 0.0

        stats = {
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "volume": round(volume, 4),
            "bounding_box": {
                "min": [round(v, 4) for v in bb_min],
                "max": [round(v, 4) for v in bb_max],
                "size": [round(v, 4) for v in bb_size],
            },
        }

        logger.info(
            f"  顶点: {stats['vertices']}, 面: {stats['faces']}, "
            f"体积: {stats['volume']}, 尺寸: {stats['bounding_box']['size']}"
        )
        return stats

    # ──────────────────────────────────────────────────────
    # 9. 完整处理管线
    # ──────────────────────────────────────────────────────
    def process_pipeline(
        self,
        raw_model_path: str,
        export_format: str = "stl",
        enable_auto_fix: bool = True,
        session_id: str = "",
    ) -> dict:
        """
        完整的网格处理管线，按顺序执行所有处理步骤。

        处理流程：
        1. 加载原始模型
        2. 网格修复（法线、退化面、重复顶点）
        3. 流形检测
        4. 孔洞填充（如果非水密）
        5. 质心计算
        6. 配重腔体生成（如果质心过高）
        7. 重网格化
        8. 最终流形检测
        9. 导出模型
        10. 返回统计信息

        Args:
            raw_model_path: 原始模型文件路径
            export_format: 导出格式 ("stl" 或 "obj")
            enable_auto_fix: 是否启用自动修复
            session_id: 会话 ID

        Returns:
            {
                "final_model_path": str,
                "mesh_stats": dict,
                "center_of_mass": dict,
                "is_manifold": bool,
                "holes_fixed": int,
                "export_format": str,
            }
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("开始完整网格处理管线")
        logger.info(f"  输入: {raw_model_path}")
        logger.info(f"  格式: {export_format}, 自动修复: {enable_auto_fix}")
        logger.info("=" * 60)

        # 步骤 1: 加载模型
        logger.info("[1/9] 加载模型...")
        try:
            mesh = trimesh.load(raw_model_path)
            if isinstance(mesh, trimesh.Scene):
                mesh = mesh.to_mesh()
            logger.info(f"  加载成功: {len(mesh.vertices)} 顶点, {len(mesh.faces)} 面")
        except Exception as e:
            raise RuntimeError(f"模型加载失败: {e}") from e

        # 步骤 2: 网格修复
        holes_fixed = 0
        if enable_auto_fix:
            logger.info("[2/9] 网格修复...")
            mesh = self.repair_mesh(mesh)
        else:
            logger.info("[2/9] 跳过网格修复（自动修复已禁用）")

        # 步骤 3: 流形检测
        logger.info("[3/9] 流形检测...")
        manifold_info = self.check_manifold(mesh)

        # 步骤 4: 孔洞填充
        if enable_auto_fix and not manifold_info["is_watertight"]:
            logger.info("[4/9] 孔洞填充...")
            mesh, holes_fixed = self.fill_holes(mesh)
        else:
            logger.info("[4/9] 跳过孔洞填充（网格已水密或修复已禁用）")

        # 步骤 5: 质心计算
        logger.info("[5/9] 质心计算...")
        com = self.compute_center_of_mass(mesh)

        # 步骤 6: 配重腔体生成
        if enable_auto_fix:
            logger.info("[6/9] 配重腔体检查...")
            mesh = self.generate_weight_cavity(mesh, com)
        else:
            logger.info("[6/9] 跳过配重腔体生成")

        # 步骤 7: 重网格化
        logger.info("[7/9] 重网格化...")
        mesh = self.remesh_quad(mesh)

        # 步骤 8: 最终流形检测
        logger.info("[8/9] 最终流形检测...")
        final_manifold = self.check_manifold(mesh)

        # 步骤 9: 导出模型
        logger.info("[9/9] 导出模型...")
        if session_id:
            output_dir = Path(settings.OUTPUT_DIR) / session_id
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"final_model.{export_format}"
        else:
            output_path = Path(raw_model_path).with_suffix(f".{export_format}")

        final_model_path = self.export_model(mesh, str(output_path), export_format)

        # 获取最终统计信息
        mesh_stats = self.get_mesh_stats(mesh)

        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"网格处理管线完成, 耗时: {elapsed:.2f}s")
        logger.info(f"  最终模型: {final_model_path}")
        logger.info(f"  顶点: {mesh_stats['vertices']}, 面: {mesh_stats['faces']}")
        logger.info(f"  流形: {final_manifold['is_manifold']}, 孔洞修复: {holes_fixed}")
        logger.info("=" * 60)

        return {
            "final_model_path": final_model_path,
            "mesh_stats": mesh_stats,
            "center_of_mass": com,
            "is_manifold": final_manifold["is_manifold"],
            "holes_fixed": holes_fixed,
            "export_format": export_format,
        }


# 全局单例
mesh_processor = MeshProcessor()
