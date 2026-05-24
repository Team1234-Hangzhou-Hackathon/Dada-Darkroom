#!/bin/bash

# 设置字符编码
export LANG=zh_CN.UTF-8

# 设置终端标题
echo -ne "\033]0;Dada-Darkroom Launcher\007"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 启动后端服务 (在后台运行)
cd "$SCRIPT_DIR"
python -m uvicorn core_modules.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 启动前端服务
cd "$SCRIPT_DIR/../frontend"
npm run dev &
FRONTEND_PID=$!

# 捕获退出信号，关闭所有子进程
cleanup() {
    echo ""
    echo "正在关闭服务..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait
    echo "Dada-Darkroom launcher 已停止。"
}
trap cleanup SIGINT SIGTERM

# 等待所有后台进程
wait
