# 3D 模型网页交互式展厅自动化管线

## 模块概述

本项目旨在实现一个“AI 图生 3D 模型，并将其自动化转换、动态集成至网页端交互式 3D 展厅”的完整 Demo 闭环。核心目标是**高弹性和自动化**，确保无论原始模型数量如何增减，整个管线都能动态扫描、处理和展示。

`backend/creative-design` 模块负责生成 `.obj` 或 `.fbx` 格式的原始 3D 模型。本模块 (`3d-gallery-demo`) 的任务是接收这些原始模型，进行自动化渲染、优化，并提供一个网页端 API 接口，最终在网页上动态展示。

## 目录结构

```
backend/3d-gallery-demo/
├── inputs/         # 存放从 AI 平台下载的任意数量原始模型 (.obj/.fbx)
├── outputs/        # 存放脚本处理完的网页专用模型 (.glb)
├── src/            # 存放前端网页代码 (index.html)
├── scripts/        # 存放自动化脚本 (process.py)
└── README.md       # 本说明文档
```

## 阶段一：运行环境检查与目录初始化 (Setup)

1.  **Blender 安装**:
    *   已确认本地已安装 Blender。
    *   Blender 可执行文件路径为：`D:/Program Files/blender/blender.exe`。
    *   虽然 `blender` 命令未加入系统 PATH，但可以通过指定完整路径来运行。
2.  **目录初始化**:
    *   已自动创建上述标准的文件夹结构。

## 阶段二：Blender 自动化加工脚本 (`scripts/process.py`)

### 脚本作用
`scripts/process.py` 是一个无界面的 Blender 后台 Python 脚本，用于自动化处理 `inputs/` 目录下的原始 3D 模型，并将其优化后导出为网页友好的 `.glb` 格式到 `outputs/` 目录。

### 脚本特性
*   **动态扫描**: 脚本运行时，自动扫描 `inputs/` 目录下所有 `.obj` 或 `.fbx` 文件，无需硬编码。
*   **场景自清洗**: 每次导入新模型前，彻底清空 Blender 默认场景中的所有对象（立方体、灯光、相机等），确保处理的独立性。
*   **网格减面优化 (Decimate)**: 为每个导入的模型自动添加“精简”修改器，并将面数压缩比率（Ratio）设为 `0.3`（保留 30% 的面数），以优化模型性能，确保网页端流畅加载。
*   **统一材质重塑 (PBR Re-texturing)**:
    *   彻底移除原始材质。
    *   创建一个全新的“原理化 BSDF (Principled BSDF)”材质球，赋予高级工业质感：
        *   基础色（浅灰色 `0.9, 0.9, 0.9, 1.0`）
        *   金属度 `1.0`
        *   粗糙度 `0.15`
*   **模型归一化**: 将模型居中，并按最大尺寸进行统一缩放，提升网页展示的一致性。
*   **规范导出**: 应用所有修改器，将处理后的模型导出至 `outputs/` 文件夹，格式为单文件二进制 `.glb`。
*   **进度日志**: 在控制台打印类似 `[Success] 1/X Processed: 文件名` 的动态进度日志。
*   **模型清单生成**: 脚本处理完成后，会在 `outputs/` 目录下生成一个 `models.json` 文件，其中包含所有成功导出的 `.glb` 模型的名称、文件路径和大小。这个 JSON 文件将作为前端动态菜单的数据源。

### 运行方式
在命令行中执行以下命令（请确保在 `backend/3d-gallery-demo` 目录下运行）：

```powershell
"D:/Program Files/blender/blender.exe" --background --python scripts/process.py
```

## 阶段三：3D 网页端展示系统 (Frontend)

### `src/index.html` (待编写)
前端代码将位于 `src/index.html`。它将实现一个交互式 3D 展厅，具备以下功能：

1.  **引入组件**: 通过 CDN 引入谷歌官方的 `<model-viewer>` 3D 核心解析库。
2.  **核心 3D 视窗配置**: `<model-viewer>` 标签将配置 `camera-controls` (允许用户旋转缩放)、`auto-rotate` (自动慢速旋转)、`shadow-intensity="1.5"` (开启高质感地面阴影)、`environment-image="neutral"` (开启标准环境反射光)。
3.  **自动化菜单生成**: 网页加载时，JavaScript 脚本将**自动读取 `outputs/models.json` 文件**，获取模型列表。然后，动态在页面上生成对应数量的点击按钮，并绑定切换事件。点击不同按钮时，动态修改 `<model-viewer>` 的 `src` 属性，实现模型的切换展示。

### 网页端 API 接口 (`outputs/models.json`)
`outputs/models.json` 文件充当了前端与后端模型数据之间的 API 接口。它由 `scripts/process.py` 脚本自动生成和更新，包含每个 `.glb` 模型的元数据，前端通过读取此文件实现动态菜单和模型加载。

## 阶段四：验证与交工 (Verification)

1.  **Blender 脚本验证**: 确保 `scripts/process.py` 能够将 `inputs/` 中的测试模型（不论数量多少）全部成功转换为 `outputs/` 中的 `.glb` 文件。
2.  **前端功能验证**: 启动一个轻量级的本地 HTTP 服务器，在浏览器中访问 `src/index.html`，检查：
    *   浏览器控制台无跨域（CORS）报错。
    *   动态生成的菜单功能完好，点击按钮能正确切换 3D 模型。
    *   3D 模型在 `<model-viewer>` 中正常显示，并具备预期的交互和视觉效果。

---

## 下一步

接下来，我将为您编写 `src/index.html` 的前端代码。
