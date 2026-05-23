import base64
import io
import logging
import os

from fastapi import FastAPI, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from PIL import Image

from app.schemas import (
    AnalyzeResponse,
    GenerateRequest,
    GenerateResponse,
    Painting,
    ProcessResponse,
)
from app.services.analyzer import analyze_mood
from app.services.generator import generate_images

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

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")


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


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if not req.prompts:
        raise HTTPException(400, "prompts 不能为空")

    images = await generate_images(req.prompts)
    return GenerateResponse(images=images)


@app.get("/")
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "MoodCanvas API is running. Frontend not found."}


if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
