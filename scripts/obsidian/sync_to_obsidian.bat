@echo off
REM 同步项目文档到Obsidian的批处理脚本
REM 这个脚本会启动自动监控模式，实时同步项目文档到Obsidian

REM 获取项目根目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..

REM 切换到项目根目录
cd %PROJECT_ROOT%

REM 激活虚拟环境（如果存在）
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM 启动同步监控
echo 正在启动文档同步监控...
python scripts/docs/obsidian/sync.py --watch

REM 等待用户输入以防止窗口立即关闭
pause
