"""
视觉分析服务 - 使用 GPT-4o 多模态能力分析灵感图像
"""
from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI
from PIL import Image
import io

from creative_design_module.app.config import settings
from creative_design_module.app.models.schemas import DesignFeatures

logger = logging.getLogger(__name__)

# 结构化提示词 - 要求模型以 JSON 格式返回设计特征
ANALYSIS_PROMPT = """你是一位资深的工业设计与艺术评论专家。请仔细分析这张抽象画作/灵感图像，提取以下设计特征，并以严格的 JSON 格式返回：

{
  "emotion_symbols": ["情感1", "象征2", ...],
  "primary_colors": ["#HEX1", "#HEX2", "#HEX3"],
  "material_guess": "推测适合的材质（如陶瓷、金属、玻璃、木材等）",
  "style_description": "详细风格描述（50-100字）",
  "structural_keywords": ["结构关键词1", "结构关键词2", ...]
}

分析要求：
1. emotion_symbols: 提取画面传达的情感和象征意义（3-6个）
2. primary_colors: 提取3-5个主要颜色的HEX值
3. material_guess: 基于画面质感推测最适合的工业制造材质
4. style_description: 描述整体风格，包括线条特征、构图方式、空间感
5. structural_keywords: 提取可用于3D建模的结构关键词（如"流线型"、"几何切割"、"有机曲面"等）

请只返回 JSON，不要包含其他文字。"""


class VisionAnalyzer:
    """GPT-4o 多模态视觉分析器"""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )

    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _resize_image_if_needed(self, image_path: str, max_size: int = 2048) -> str:
        """如果图片过大则压缩，返回处理后的路径"""
        img = Image.open(image_path)
        if max(img.size) <= max_size:
            return image_path

        ratio = max_size / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

        # 保存为临时文件
        output_path = str(Path(image_path).with_suffix(".resized.jpg"))
        img.convert("RGB").save(output_path, "JPEG", quality=90)
        return output_path

    async def analyze_inspiration(self, image_path: str) -> DesignFeatures:
        """
        分析灵感图像，提取设计特征。

        Args:
            image_path: 灵感图像文件路径

        Returns:
            DesignFeatures 结构化设计特征
        """
        logger.info(f"开始分析灵感图像: {image_path}")

        # 预处理图片
        processed_path = self._resize_image_if_needed(image_path)
        base64_image = self._encode_image(processed_path)

        # 调用 GPT-4o Vision API
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": ANALYSIS_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=1024,
                temperature=0.3,
            )
        except Exception as e:
            logger.error(f"GPT-4o API 调用失败: {e}")
            raise RuntimeError(f"视觉分析服务调用失败: {e}") from e

        # 解析响应
        content = response.choices[0].message.content.strip()
        logger.debug(f"GPT-4o 响应: {content}")

        try:
            # 尝试直接解析 JSON
            # 处理可能的 markdown 代码块包裹
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            features = DesignFeatures(
                emotion_symbols=data.get("emotion_symbols", []),
                primary_colors=data.get("primary_colors", []),
                material_guess=data.get("material_guess", ""),
                style_description=data.get("style_description", ""),
                structural_keywords=data.get("structural_keywords", []),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"解析 GPT-4o 响应失败: {e}, 原始内容: {content}")
            # 返回默认特征而非抛出异常，保证管线继续运行
            features = DesignFeatures(
                emotion_symbols=["抽象"],
                primary_colors=["#888888"],
                material_guess="陶瓷",
                style_description=content[:200] if content else "无法解析风格",
                structural_keywords=["有机形态"],
            )

        logger.info(f"分析完成 - 情感: {features.emotion_symbols}, 材质: {features.material_guess}")
        return features


# 全局单例
vision_analyzer = VisionAnalyzer()
