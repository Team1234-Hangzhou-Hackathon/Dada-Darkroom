# DADA DARKROOM API 接口文档

## 基础信息

- **Base URL**: `http://localhost:3001/api` (可根据实际部署调整)
- **Content-Type**: `application/json`

---

## 1. 生成荒诞派图片

### 接口地址
```
POST /generate-dada-images
```

### 请求参数
```json
{
  "image": "string (base64 或 URL)",
  "description": "string (用户输入的荒诞感受描述)"
}
```

### 响应格式
```json
{
  "success": true,
  "images": [
    "https://example.com/generated-image-1.jpg",
    "https://example.com/generated-image-2.jpg",
    "https://example.com/generated-image-3.jpg",
    "https://example.com/generated-image-4.jpg"
  ]
}
```

### 说明
- 接收用户上传的图片和描述文本
- 使用 Claude API 分析图片并生成 4 张荒诞派风格的图片
- 返回 4 张生成图片的 URL

---

## 2. 生成创意产品

### 接口地址
```
POST /generate-product
```

### 请求参数
```json
{
  "selectedImage": "string (用户选中的图片URL)",
  "description": "string (用户输入的荒诞感受描述)"
}
```

### 响应格式
```json
{
  "success": true,
  "product": {
    "type": "string (产品类型，如：解构主义帆布袋)",
    "description": "string (AI生成的产品描述)",
    "previewImage": "string (产品预览图URL)",
    "elements": ["string", "string", "string"] (提取的设计元素标签)
  }
}
```

### 说明
- 接收用户选中的荒诞派图片
- 使用 Claude API 分析图片特色元素
- 生成创意产品建议和描述
- 返回产品类型、描述、预览图和提取的设计元素

---

## 前端对接说明

### 当前模拟代码位置
文件：`frontend/src/App.jsx`

### 需要修改的代码

1. **修改 API_BASE_URL**（第20行）：
```javascript
const API_BASE_URL = 'http://your-backend-url/api';
```

2. **取消注释真实API调用代码**：
- `handleGenerate` 函数（第26-36行）
- `handleSelectImage` 函数（第61-71行）

3. **删除模拟代码**：
- 第38-45行（模拟生成图片）
- 第73-99行（模拟生成产品）

---

## Claude API 使用建议

### 图片分析 Prompt 示例

**生成荒诞派图片：**
```
分析这张图片，提取其视觉元素、色彩、构图特点。
根据用户描述"{description}"，生成4张荒诞派风格的变体图片。
要求：
1. 保持原图的核心元素
2. 加入达达主义的拼贴、错位、反逻辑特征
3. 使用对比强烈的色彩
4. 创造视觉张力和荒诞感
```

**生成创意产品：**
```
分析这张荒诞派图片，提取其核心设计元素。
基于这些元素，设计一个创意文创产品。
返回：
1. 产品类型（帆布袋/手机壳/徽章/海报等）
2. 产品描述（50字以内）
3. 提取的3个设计元素标签
```

---

## 错误处理

### 错误响应格式
```json
{
  "success": false,
  "error": "错误信息描述"
}
```

### 前端已实现错误处理
- 网络请求失败时显示 alert 提示
- 控制台输出详细错误信息

---

## 测试建议

1. 先测试 `/generate-dada-images` 接口
2. 确认返回4张图片URL格式正确
3. 再测试 `/generate-product` 接口
4. 确认产品数据结构符合预期

---

## 联系方式

如有问题，请联系前端开发者。
