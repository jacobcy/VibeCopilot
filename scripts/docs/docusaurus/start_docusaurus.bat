@echo off
REM 启动Docusaurus开发服务器的批处理脚本
REM 同时执行文档同步和Docusaurus服务器启动

REM 获取项目根目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..\..

REM 切换到项目根目录
cd %PROJECT_ROOT%

REM 激活虚拟环境（如果存在）
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM 检查website目录是否存在
if not exist website (
    echo 错误: 未找到website目录，确保Docusaurus已正确安装
    exit /b 1
)

REM 检查依赖是否已安装
if not exist website\node_modules (
    echo 安装Docusaurus依赖...
    cd website
    call npm install
    cd ..
)

REM 生成侧边栏配置
echo 正在生成侧边栏配置...
python scripts/docs/obsidian_sync.py --sidebar --output website/sidebars.json

REM 启动同步监控（新窗口）
echo 启动文档同步监控...
start "Docs Sync" cmd /c python scripts/docs/obsidian_sync.py --watch

REM 启动Docusaurus开发服务器
echo 启动Docusaurus开发服务器...
cd website
npm run start

REM 如果Docusaurus服务器退出，通知用户如何终止同步进程
echo Docusaurus服务器已停止，请手动关闭文档同步窗口
pause
