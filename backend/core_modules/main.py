import base64
import io
import logging
import os
import subprocess
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from PIL import Image

from core_modules.schemas import (
    AnalyzeResponse,
    GenerateRequest,
    GenerateResponse,
    Painting,
    ProcessResponse,
)
from core_modules.services.analyzer import analyze_mood
from core_modules.services.generator import generate_images

# 导入 creative-design 模块的路由
from creative_design_module.app.routers import stage1_analyze, stage2_modify, stage3_generate, stage4_finalize
from creative_design_module.app.models.schemas import MaterialSettings
from creative_design_module.app.services.mesh_processor import mesh_processor
from creative_design_module.app.services.multiview_generator import multiview_generator
from creative_design_module.app.services.reconstruction_3d import reconstruction_3d
from creative_design_module.app.services.texture_service import texture_service
from creative_design_module.app.services.vision_analyzer import vision_analyzer
from creative_design_module.app.utils.file_manager import (
    create_session_dir,
    get_session_output_dir,
    get_session_upload_dir,
    save_upload_file,
    sync_model_to_gallery,
)

logging.basicConfig(level=logging.INFO)


def compress_image(image_bytes: bytes, max_size: int = 1024) -> str:
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode == "RGBA":
        img = img.convert("RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


app = FastAPI(title="MoodCanvas API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static")
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/process", response_model=ProcessResponse)
async def process(image: bytes = File(...), text: str = Form(...)):
    if not text.strip():
        raise HTTPException(400, "文字描述不能为空")

    image_b64 = compress_image(image)

    try:
        result = await analyze_mood(image_b64, text)
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    prompts = [p.prompt for p in result["paintings"]]
    images = await generate_images(prompts)

    paintings = []
    for painting, img in zip(result["paintings"], images):
        paintings.append(
            Painting(
                title=painting.title,
                prompt=painting.prompt,
                image_url=img.get("image_url"),
            )
        )

    return ProcessResponse(emotion=result["emotion"], paintings=paintings)


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(image: bytes = File(...), text: str = Form(...)):
    if not text.strip():
        raise HTTPException(400, "文字描述不能为空")

    image_b64 = compress_image(image)
    try:
        result = await analyze_mood(image_b64, text)
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    return AnalyzeResponse(emotion=result["emotion"], paintings=result["paintings"])


@app.post("/api/creative-design/auto")
async def creative_design_auto(
    image: UploadFile = File(...),
    text: str = Form(...),
):
    if not text.strip():
        raise HTTPException(400, "文字描述不能为空")
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "请上传图片文件")

    session_id = create_session_dir()
    upload_dir = get_session_upload_dir(session_id)
    output_dir = get_session_output_dir(session_id)

    try:
        inspiration_path = await save_upload_file(image, upload_dir, filename="inspiration.png")
        design_features = await vision_analyzer.analyze_inspiration(inspiration_path)
        multi_view_paths = await multiview_generator.generate_multi_view(
            image_path=inspiration_path,
            design_features=design_features,
            session_id=session_id,
        )
        if not multi_view_paths:
            raise RuntimeError("多视角生成失败")

        selected_view_index = 0
        view_path = Path(multi_view_paths[selected_view_index])
        mask_path = output_dir / "mask.png"
        if not mask_path.exists():
            from PIL import Image as PILImage
            base_img = PILImage.open(view_path)
            mask_img = PILImage.new("L", base_img.size, 255)
            mask_img.save(mask_path)

        updated_view_path = await inpainting_service.inpaint_view(
            view_path=str(view_path),
            mask_path=str(mask_path),
            prompt=text,
            session_id=session_id,
        )
        updated_multi_view_paths = await inpainting_service.propagate_changes(
            modified_view_path=updated_view_path,
            other_view_paths=[p for i, p in enumerate(multi_view_paths) if i != selected_view_index],
            prompt=text,
            session_id=session_id,
        )

        raw_model_path = await reconstruction_3d.generate_mesh(
            multi_view_paths=updated_multi_view_paths,
            session_id=session_id,
        )
        texture_paths = await texture_service.generate_pbr_textures(
            mesh_path=raw_model_path,
            material_settings=MaterialSettings(),
            session_id=session_id,
        )
        final_result = mesh_processor.process_pipeline(
            raw_model_path=raw_model_path,
            export_format="glb",
            enable_auto_fix=True,
            session_id=session_id,
        )
        gallery_sync = sync_model_to_gallery(final_result["final_model_path"], session_id)

        gallery_root = Path(__file__).resolve().parents[1] / "3d_gallery_demo_module"
        subprocess.run(
            [
                "blender",
                "--background",
                "--python",
                str(gallery_root / "scripts" / "process.py"),
            ],
            cwd=str(gallery_root),
            check=False,
        )

        return {
            "session_id": session_id,
            "design_features": design_features.model_dump(),
            "multi_view_paths": multi_view_paths,
            "updated_multi_view_paths": updated_multi_view_paths,
            "raw_model_path": raw_model_path,
            "texture_paths": texture_paths,
            "final_model_path": final_result["final_model_path"],
            "mesh_stats": final_result["mesh_stats"],
            "gallery_sync": gallery_sync,
            "gallery_manifest": str(gallery_root / "outputs" / "models.json"),
        }
    except Exception as e:
        raise HTTPException(502, str(e))



@app.get("/")
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "MoodCanvas API is running. Frontend not found."}


@app.get("/favicon.svg")
async def serve_favicon():
    return FileResponse(os.path.join(STATIC_DIR, "favicon.svg"))


@app.get("/icons.svg")
async def serve_icons():
    return FileResponse(os.path.join(STATIC_DIR, "icons.svg"))


app.mount("/assets", StaticFiles(directory=ASSETS_DIR, check_dir=False), name="assets")

# 注册 creative-design 模块的路由
app.include_router(stage1_analyze.router, prefix="/creative-design")
app.include_router(stage2_modify.router, prefix="/creative-design")
app.include_router(stage3_generate.router, prefix="/creative-design")
app.include_router(stage4_finalize.router, prefix="/creative-design")
