# Dada-Darkroom 项目设置

## 概述

这是一个包含前端 (React) 和后端 (FastAPI) 的全栈项目。

## 安装

### 后端 (Backend)

1.  **Python 虚拟环境**:
    请确保您的系统已安装 Python 3.8+。
    建议手动创建并激活虚拟环境：
    ```powershell
    # 在 backend 目录下 (Windows)
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```
    ```bash
    # 在 backend 目录下 (Linux/macOS)
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  **安装依赖**:
    激活虚拟环境后，安装 `requirements.txt` 中列出的依赖：
    ```powershell
    # 在 backend 目录下 (Windows)
    pip install -r requirements.txt
    ```
    ```bash
    # 在 backend 目录下 (Linux/macOS)
    pip install -r requirements.txt
    ```

### 前端 (Frontend)

1.  **安装依赖**:
    在 `frontend` 目录下运行以下命令安装 Node.js 依赖：
    ```bash
    npm install
    ```

## 启动项目

### Windows

在 `backend` 目录下，打开 PowerShell 终端并执行以下命令：
```powershell
.\start.ps1
```

### Linux/macOS

在 `backend` 目录下，打开终端并执行以下命令：
```bash
chmod +x start.sh
./start.sh
```

以上脚本将同时启动 FastAPI 后端服务和 Vite 前端开发服务器。按 `Ctrl+C` 可停止所有服务。

## 结束服务脚本

停止脚本已强化，可用于一键结束由启动脚本拉起的 FastAPI 后端服务和 Vite 前端开发服务器。

### Windows

在 `backend` 目录下，打开 PowerShell 终端并执行以下命令：
```powershell
.\stop.ps1
```

### Linux/macOS

在 `backend` 目录下，打开终端并执行以下命令：
```bash
chmod +x stop.sh
./stop.sh
```

以上脚本会尝试终止相关的后端 Python 进程和前端 Node.js 进程，方便在测试后快速结束服务。

## Git 初始化

项目已初始化为 Git 仓库，并配置了 `.gitignore` 文件以忽略虚拟环境和 Node.js 依赖文件。
