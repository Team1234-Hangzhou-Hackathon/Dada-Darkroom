# 设置字符编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "正在停止 Dada-Darkroom 服务..."

# 停止后端 Python 进程 (uvicorn)
Get-CimInstance Win32_Process |
    Where-Object { $_.Name -eq "python.exe" -and $_.CommandLine -like "*uvicorn core_modules.main:app*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# 停止前端 Node.js 进程 (npm run dev)
Get-CimInstance Win32_Process |
    Where-Object { $_.Name -eq "node.exe" -and $_.CommandLine -like "*npm run dev*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Write-Host "服务停止完成。"
Write-Host "按任意键关闭此窗口。"
Pause | Out-Null
