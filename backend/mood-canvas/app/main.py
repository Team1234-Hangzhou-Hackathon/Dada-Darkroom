import base64
import logging

from fastapi import FastAPI, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    AnalyzeResponse,
    EmotionResult,
    GenerateRequest,
    GenerateResponse,
    Painting,
    ProcessResponse,
)
from app.services.analyzer import analyze_mood
from app.services.generator import generate_images

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="MoodCanvas API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/process", response_model=ProcessResponse)
async def process(image: bytes = File(...), text: str = Form(...)):
    if not text.strip():
        raise HTTPException(400, "文字描述不能为空")

    image_b64 = base64.b64encode(image).decode()

    result = await analyze_mood(image_b64, text)

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

    image_b64 = base64.b64encode(image).decode()
    result = await analyze_mood(image_b64, text)

    return AnalyzeResponse(emotion=result["emotion"], paintings=result["paintings"])


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if not req.prompts:
        raise HTTPException(400, "prompts 不能为空")

    images = await generate_images(req.prompts)
    return GenerateResponse(images=images)
