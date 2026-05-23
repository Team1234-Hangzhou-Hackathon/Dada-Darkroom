# MoodCanvas - 情绪抽象画生成器

> 打破快 shutter 界限：多模态智能交互下的生成式体验

## 项目简介
用户上传一张图片并输入文字描述当前心情，AI 通过视觉理解 + 语义分析综合判断情绪状态，据此生成 5 张风格各异的抽象画作供用户挑选。

## 技术架构
- **后端**: Python FastAPI
- **AI 模型**: GPT-5.5 (图片理解 + 情绪分析) + DALL-E (抽象画生成)
- **语音输入**: 浏览器 Web Speech API

## 快速开始
```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入你的 OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```
打开 http://localhost:8000/docs 查看 API 文档并测试。

## API 接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/process` | POST | 完整流程：图片+文字 → 情绪分析 → 5张抽象画 |
| `/api/analyze` | POST | 仅情绪分析（不含图片生成）|
| `/api/generate` | POST | 仅图片生成（传入 prompt 列表）|

## 团队
黑客松参赛作品
