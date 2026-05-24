# 前后端对接指南

## 概述

本项目前端已完整实现所有功能逻辑，预留了2个核心API接口供后端AI服务对接。

---

## ✅ 已确认的功能流程

### 1. 点击"解构现实"按钮 → 生成荒诞派图片

**前端状态**：`isGenerating`
**触发函数**：`handleGenerate()`（第122行）
**当前行为**：
- 显示"PROCESSING..."加载状态
- 调用API生成4张图片
- 更新 `generatedImages` 状态
- 图片显示在下方网格中

**预留API**：
```
POST /generate-dada-images
```

**请求数据**：
```javascript
{
  image: "base64字符串或URL",
  description: "用户输入的荒诞感受描述"
}
```

**预期响应**：
```javascript
{
  success: true,
  images: [
    "生成的图片URL1",
    "生成的图片URL2", 
    "生成的图片URL3",
    "生成的图片URL4"
  ]
}
```

---

### 2. 用户点击选择某张图片 → AI创意工坊生成产品

**前端状态**：`isGeneratingProduct`, `generatedProduct`
**触发函数**：`handleSelectImage(imgUrl)`（第153行）
**当前行为**：
- 自动标记选中的图片（黄色边框）
- 显示"AI正在解构你的选择..."加载动画
- 调用API生成创意产品
- 展示产品信息：
  - 产品类型
  - 产品描述
  - 提取的设计元素标签
  - 产品预览图

**预留API**：
```
POST /generate-product
```

**请求数据**：
```javascript
{
  selectedImage: "用户选中的图片URL",
  description: "用户输入的荒诞感受描述"
}
```

**预期响应**：
```javascript
{
  success: true,
  product: {
    type: "产品类型（如：解构主义帆布袋）",
    description: "AI生成的产品描述（50字以内）",
    previewImage: "产品预览图URL",
    elements: ["元素1", "元素2", "元素3"]  // 提取的3个设计元素标签
  }
}
```

---

## 🔧 后端对接步骤

### 步骤1：修改API地址

打开文件：`frontend/src/App.jsx`

找到第116行：
```javascript
const API_BASE_URL = 'http://localhost:3001/api';
```

替换为你的后端实际地址：
```javascript
const API_BASE_URL = 'http://your-backend-server.com/api';
```

### 步骤2：启用真实API调用

找到 `handleGenerate` 函数（约第122行），删除模拟代码，取消注释真实API调用：

```javascript
const handleGenerate = async () => {
  setIsGenerating(true);
  
  try {
    // 取消注释这段代码
    const response = await fetch(`${API_BASE_URL}/generate-dada-images`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image: uploadedImage,
        description: userDescription
      })
    });
    const data = await response.json();
    setGeneratedImages(data.images);

    // 删除下面的模拟代码
    // await new Promise(resolve => setTimeout(resolve, 2000));
    // setGeneratedImages([...]);
  } catch (error) {
    console.error('生成图片失败:', error);
    alert('生成图片失败，请重试');
  } finally {
    setIsGenerating(false);
  }
};
```

### 步骤3：启用产品生成API

找到 `handleSelectImage` 函数（约第153行），同样操作：

```javascript
const handleSelectImage = async (imgUrl) => {
  setSelectedImage(imgUrl);
  setIsGeneratingProduct(true);
  setGeneratedProduct(null);

  try {
    // 取消注释这段代码
    const response = await fetch(`${API_BASE_URL}/generate-product`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        selectedImage: imgUrl,
        description: userDescription
      })
    });
    const data = await response.json();
    setGeneratedProduct(data.product);

    // 删除下面的模拟代码和mockProducts数组
  } catch (error) {
    console.error('生成产品失败:', error);
    alert('生成产品失败，请重试');
  } finally {
    setIsGeneratingProduct(false);
  }
};
```

---

## 📋 后端需要实现的API

### API 1: 生成荒诞派图片

**端点**：`POST /generate-dada-images`

**推荐实现**：
```python
# Python/Flask 示例
@app.route('/api/generate-dada-images', methods=['POST'])
def generate_dada_images():
    data = request.json
    image = data['image']  # base64或URL
    description = data['description']
    
    # 调用 Claude API 处理
    # 生成4张荒诞派风格的图片
    
    return jsonify({
        'success': True,
        'images': [
            'https://your-server.com/generated/1.jpg',
            'https://your-server.com/generated/2.jpg',
            'https://your-server.com/generated/3.jpg',
            'https://your-server.com/generated/4.jpg'
        ]
    })
```

**Claude API 提示词建议**：
```
分析这张图片的视觉元素、色彩、构图特点。
根据用户描述"{description}"，生成4张荒诞派风格的变体图片。
要求：
1. 保持原图的核心元素
2. 加入达达主义的拼贴、错位、反逻辑特征
3. 使用对比强烈的色彩
4. 创造视觉张力和荒诞感
```

---

### API 2: 生成创意产品

**端点**：`POST /generate-product`

**推荐实现**：
```python
@app.route('/api/generate-product', methods=['POST'])
def generate_product():
    data = request.json
    selected_image = data['selectedImage']  # 用户选中的图片URL
    description = data['description']       # 用户的荒诞感受描述
    
    # 调用 Claude API 分析
    # 提取设计元素
    # 生成创意产品
    
    return jsonify({
        'success': True,
        'product': {
            'type': '解构主义帆布袋',
            'description': '提取了图片中的几何碎片元素...',
            'previewImage': 'https://your-server.com/product-preview.jpg',
            'elements': ['几何碎片', '错位构图', '荒诞色彩']
        }
    })
```

**Claude API 提示词建议**：
```
分析这张荒诞派图片，提取其核心设计元素。
基于这些元素，设计一个创意文创产品。
返回：
1. 产品类型（帆布袋/手机壳/徽章/海报等）
2. 产品描述（50字以内）
3. 提取的3个设计元素标签
```

---

## ⚠️ 注意事项

1. **CORS问题**：确保后端配置了CORS，允许前端域名访问
   ```python
   from flask_cors import CORS
   CORS(app, resources={r"/api/*": {"origins": "*"}})
   ```

2. **图片格式**：前端支持base64和URL两种格式

3. **错误处理**：后端返回错误时，前端会显示alert提示

4. **加载状态**：前端会自动显示加载动画，无需额外处理

5. **图片预览**：生成的产品预览图会显示在AI创意工坊区域

---

## 🎯 测试建议

1. 先单独测试 `/generate-dada-images` 接口
2. 确认返回4张图片URL格式正确
3. 再测试 `/generate-product` 接口
4. 确认产品数据结构符合预期
5. 逐步替换前端模拟代码

---

## 📞 联系方式

如有API对接问题，请联系前端开发者。
