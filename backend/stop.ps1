# 设置字符编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "正在停止 Dada-Darkroom 服务..."

# 停止后端 Python 进程 (uvicorn)
Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*uvicorn core_modules.main:app*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 停止前端 Node.js 进程 (npm run dev)
Get-Process | Where-Object { $_.ProcessName -eq "node" -and $_.CommandLine -like "*npm run dev*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "服务停止完成。"
Write-Host "按任意键关闭此窗口。"
Pause | Out-Null
