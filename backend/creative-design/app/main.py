"""
FastAPI 应用入口 - 创意设计管线后端服务
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import stage1_analyze, stage2_modify, stage3_generate, stage4_finalize

# ──────────────────────────────────────────────
# 日志配置
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 应用生命周期
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的生命周期管理"""
    logger.info("=" * 60)
    logger.info("创意设计管线服务启动中...")
    logger.info(f"上传目录: {settings.upload_path}")
    logger.info(f"输出目录: {settings.output_path}")
    logger.info("=" * 60)

    # 确保必要目录存在
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.output_path.mkdir(parents=True, exist_ok=True)

    yield

    logger.info("创意设计管线服务已关闭")


# ──────────────────────────────────────────────
# FastAPI 应用实例
# ──────────────────────────────────────────────
app = FastAPI(
    title="创意设计管线 API",
    description="""
    创意设计管线后端服务 - 4 阶段工业设计自动化管线

    ## 管线流程
    1. **阶段一 - 分析与演化**: 上传灵感图像 → AI 分析设计特征 → 生成多视角图像
    2. **阶段二 - 设计修改**: 选择视角 → 蒙版标注 → AI Inpainting → 风格传播
    3. **阶段三 - 3D 重建**: 多视角 → TRELLIS 3D 重建 → Meshy PBR 纹理
    4. **阶段四 - 修复导出**: 网格修复 → 流形检测 → 孔洞填充 → 配重优化 → STL/OBJ 导出
    """,
    version="1.0.0",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────
# CORS 中间件
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# 全局异常处理
# ──────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"},
    )


# ──────────────────────────────────────────────
# 注册路由
# ──────────────────────────────────────────────
app.include_router(stage1_analyze.router)
app.include_router(stage2_modify.router)
app.include_router(stage3_generate.router)
app.include_router(stage4_finalize.router)


# ──────────────────────────────────────────────
# 健康检查
# ──────────────────────────────────────────────
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "creative-design-pipeline"}


@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "service": "创意设计管线 API",
        "version": "1.0.0",
        "docs": "/docs",
    }
