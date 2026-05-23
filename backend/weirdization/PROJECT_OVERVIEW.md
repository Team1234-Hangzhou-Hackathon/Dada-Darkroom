# MoodCanvas 项目介绍与 API 说明

## 1. 项目是什么

MoodCanvas 是一个“情绪抽象画生成器”。用户上传一张图片，再输入一段描述当前感受的文字，系统会：

1. 理解图片内容与用户文字表达的情绪。
2. 输出主要情绪、次要情绪、情绪强度与推荐色彩。
3. 生成 5 条抽象画创作提示词。
4. 根据提示词生成 5 张抽象画图片，供用户选择与下载。

该项目包含一个 FastAPI 后端和一个静态网页前端，适合用于黑客松展示、多模态交互演示或生成式艺术体验原型。

## 2. 当前已经实现的功能

| 功能 | 说明 |
| --- | --- |
| 图片上传预览 | 用户可在网页中上传 JPG、PNG、WEBP 图片，并立即看到预览 |
| 文字心情输入 | 用户输入对当下心情或场景的描述 |
| 语音输入 | 前端使用浏览器 Web Speech API，将中文语音转为文字 |
| 图片与文字联合分析 | 后端将上传图片压缩后，与用户文字一起发送给视觉理解模型 |
| 情绪结构化输出 | 返回主要情绪、次要情绪、强度和色彩方案 |
| 抽象画提示词生成 | AI 为同一情绪内核生成 5 条风格略有差异的英文图片提示词 |
| 图片生成 | 根据每条提示词生成一张抽象画 |
| 作品选择与下载 | 用户可选择喜欢的生成图，并在页面中触发下载 |
| 健康检查 | 提供接口确认后端是否正常启动 |
| API 调试文档 | FastAPI 自动提供 Swagger 页面用于接口测试 |

## 3. 当前使用了哪些外部 API

当前代码实现使用的是 **智谱 AI 开放平台 API**，通过 Python 包 `zhipuai` 发起请求。

> 注意：团队曾讨论迁移到阿里云百炼，但当前代码并未接入百炼。本文以下说明均以现有代码为准。

### 3.1 图片理解与情绪分析 API

| 项目 | 内容 |
| --- | --- |
| 服务提供方 | 智谱 AI |
| 配置项 | `ZHIPU_VISION_MODEL` |
| 当前默认模型 | `glm-4v-flash` |
| 调用位置 | `app/services/analyzer.py` |
| 输入 | 压缩后的图片 Base64 + 用户心情文字 |
| 输出 | 情绪 JSON 和 5 条抽象画 Prompt |

后端要求模型返回如下结构：

```json
{
  "emotion": {
    "primary": "宁静",
    "secondary": "希望",
    "intensity": 0.7,
    "color_palette": ["深蓝色", "金色", "暖橙色"]
  },
  "paintings": [
    {
      "title": "暮光之舞",
      "prompt": "Abstract painting, flowing indigo layers with warm golden light..."
    }
  ]
}
```

为了适配免费视觉模型的输出长度限制，当前 Prompt 模板要求每条画面描述保持简短，并将最大输出设置为 `1024` tokens。

### 3.2 抽象画图片生成 API

| 项目 | 内容 |
| --- | --- |
| 服务提供方 | 智谱 AI |
| 配置项 | `ZHIPU_IMAGE_MODEL` |
| 当前默认模型 | `cogview-3-flash` |
| 调用位置 | `app/services/generator.py` |
| 输入 | 英文抽象画 Prompt |
| 输出 | 可在浏览器展示的图片 URL |

一次完整创作需要生成 5 张图片。当前实现会依次请求图片生成模型，而不是同时并发发送全部请求。

为降低限流导致的失败概率，代码中实现了：

- 相邻图片请求之间等待 `2` 秒。
- 遇到含 `429` 或 `1302` 的限流错误时，按照 `5` 秒、`10` 秒、`20` 秒的间隔重试。
- 单张图片最终失败时返回空图片地址，避免整个接口因某一张失败而直接崩溃。

## 4. 完整数据流程

```text
用户上传图片 + 输入心情文字
          |
          v
浏览器 POST /api/process
          |
          v
后端将图片压缩为 JPEG Base64
          |
          v
glm-4v-flash 分析图片与文字
          |
          v
返回情绪信息 + 5 条英文抽象画 Prompt
          |
          v
cogview-3-flash 逐张生成图片
          |
          v
后端返回情绪结果 + 5 张图片 URL
          |
          v
网页展示作品，用户选择并下载
```

## 5. 本项目提供的后端接口

服务启动后，可打开 `http://127.0.0.1:8000/docs` 查看并在线测试全部接口。

### 5.1 健康检查

```http
GET /api/health
```

返回示例：

```json
{
  "status": "ok"
}
```

### 5.2 完整创作流程

```http
POST /api/process
Content-Type: multipart/form-data
```

表单参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `image` | 文件 | 用户上传的图片 |
| `text` | 字符串 | 用户输入的心情描述，不能为空 |

返回内容：

- 情绪分析结果。
- 5 幅画作的标题。
- 5 条生成提示词。
- 每幅画对应的图片 URL。

### 5.3 仅分析图片和情绪

```http
POST /api/analyze
Content-Type: multipart/form-data
```

适用于只想查看情绪识别与画作提示词，而暂时不生成图片的场景。

### 5.4 仅根据 Prompt 生成图片

```http
POST /api/generate
Content-Type: application/json
```

请求示例：

```json
{
  "prompts": [
    "Abstract painting, indigo waves with soft golden light and quiet flowing texture."
  ]
}
```

返回图片生成结果列表。

## 6. 项目目录说明

```text
backend/
|-- app/
|   |-- main.py                 # FastAPI 入口、接口路由、图片压缩
|   |-- config.py               # 环境变量与模型配置
|   |-- schemas.py              # 请求与响应数据模型
|   |-- prompts/
|   |   `-- mood_art.py         # 情绪分析和画作生成提示词模板
|   `-- services/
|       |-- analyzer.py         # 图片理解、情绪分析调用
|       `-- generator.py        # 图片生成、限流等待与重试
|-- static/
|   `-- index.html              # 网页界面
|-- tests/                      # 自动化回归测试
|-- .env.example                # 配置模板，不包含真实 Key
|-- requirements.txt            # Python 依赖
`-- README.md                   # 简要说明
```

## 7. 环境配置

复制配置模板：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`：

```env
ZHIPU_API_KEY=你的智谱APIKey
ZHIPU_VISION_MODEL=glm-4v-flash
ZHIPU_IMAGE_MODEL=cogview-3-flash
```

安全要求：

- 不要把真实 API Key 写入 `README` 或本文档。
- 不要把包含真实 Key 的 `.env` 上传到公开仓库。
- 若 Key 曾在聊天、截图或提交记录中暴露，应立即在平台控制台轮换。

## 8. 启动方法

在 `backend` 目录执行：

```powershell
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

打开页面：

```text
http://127.0.0.1:8000/
```

打开 API 文档：

```text
http://127.0.0.1:8000/docs
```

## 9. 已知限制与后续改进方向

### 当前限制

- 公共免费模型可能因平台繁忙或频率限制返回错误，不能承诺每次生成都成功。
- 完整流程需要生成 5 张图片，因此等待时间比单图生成更长。
- 视觉模型输出必须是合法 JSON；如果模型返回内容不完整，解析会失败。

### 推荐改进

- 前端将上游繁忙提示展示为“模型繁忙，请稍后重试”，避免仅显示笼统的 `500`。
- 在生产环境使用具有明确配额和提额机制的付费模型服务。
- 若后续迁移到阿里云百炼，可考虑使用视觉模型进行分析，并使用支持单次多图输出的生图模型，以减少重复调用和限流风险。

## 10. 一句话介绍

MoodCanvas 是一个以图片与文字共同识别情绪、再通过生成式 AI 创作五幅抽象画的多模态艺术交互应用。
