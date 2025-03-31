@echo off
REM 一次性同步所有文档的批处理脚本
REM 这个脚本会执行一次完整的双向同步

REM 获取项目根目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..

REM 切换到项目根目录
cd %PROJECT_ROOT%

REM 激活虚拟环境（如果存在）
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM 执行同步
echo 开始同步所有文档...
python scripts/docs/obsidian/sync.py --sync-all

REM 等待用户输入以防止窗口立即关闭
echo 同步完成。按任意键退出...
pause
