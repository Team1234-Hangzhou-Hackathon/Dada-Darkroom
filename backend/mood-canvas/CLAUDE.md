# MoodCanvas 后端

情绪抽象画生成 API 服务。

## 启动
```bash
pip install -r requirements.txt
cp .env.example .env  # 填入 API key
uvicorn app.main:app --reload --port 8000
```

## API 文档
启动后访问 `http://localhost:8000/docs`

## 项目结构
- `app/main.py` — FastAPI 入口，路由
- `app/schemas.py` — 请求/响应数据模型
- `app/config.py` — 配置管理
- `app/services/analyzer.py` — GPT-5.5 情绪分析
- `app/services/generator.py` — DALL-E 图片生成
- `app/prompts/mood_art.py` — Prompt 模板
