import base64
import io
import logging
import os

from fastapi import FastAPI, File, Form, HTTPException
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
    image: bytes = File(...),
    text: str = Form(...),
):
    if not text.strip():
        raise HTTPException(400, "文字描述不能为空")

    image_b64 = compress_image(image)

    try:
        stage1 = await stage1_analyze.stage1_analyze(image=image, text=text)
        stage2 = await stage2_modify.stage2_modify(
            session_id=stage1["session_id"],
            image=image,
        )
        stage3 = await stage3_generate.stage3_generate(
            session_id=stage1["session_id"],
            prompt=text,
        )
        stage4 = await stage4_finalize.stage4_finalize(
            session_id=stage1["session_id"],
        )
    except Exception as e:
        raise HTTPException(502, str(e))

    return {
        "session_id": stage1["session_id"],
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3,
        "stage4": stage4,
        "gallery_url": stage4.get("gallery_url"),
        "model_url": stage4.get("model_url"),
    }



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
