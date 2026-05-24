#!/bin/bash

# 设置字符编码
export LANG=zh_CN.UTF-8

echo "正在停止 Dada-Darkroom 服务..."

# 停止后端 Python 进程 (uvicorn)
pkill -f "uvicorn core_modules.main:app"

# 停止前端 Node.js 进程 (npm run dev)
pkill -f "npm run dev"

echo "服务停止完成。"
