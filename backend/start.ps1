# 设置字符编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 设置窗口标题
$Host.UI.RawUI.WindowTitle = "Dada-Darkroom Launcher"

# 启动后端服务 (在后台运行)
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"cd $PSScriptRoot; python -m uvicorn core_modules.main:app --host 0.0.0.0 --port 8000`""

# 启动前端服务
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"cd $PSScriptRoot\..\frontend; .\start.ps1`""

Write-Host ""
Write-Host "Dada-Darkroom launcher 已停止。请检查上面的消息或 startup-error.log。"
Write-Host "按任意键关闭此窗口。"
Pause | Out-Null
