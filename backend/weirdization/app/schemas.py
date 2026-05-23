from pydantic import BaseModel


class EmotionResult(BaseModel):
    primary: str
    secondary: str
    intensity: float
    color_palette: list[str]


class Painting(BaseModel):
    title: str
    prompt: str
    image_url: str | None = None


class AnalyzeResponse(BaseModel):
    emotion: EmotionResult
    paintings: list[Painting]


class ProcessResponse(BaseModel):
    emotion: EmotionResult
    paintings: list[Painting]


class GenerateRequest(BaseModel):
    prompts: list[str]


class GenerateResponse(BaseModel):
    images: list[dict]
