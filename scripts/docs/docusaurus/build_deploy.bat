@echo off
REM 构建和部署Docusaurus网站的批处理脚本

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

REM 同步所有文档
echo 正在同步文档...
python scripts/docs/obsidian_sync.py --sync-all

REM 验证链接
echo 验证文档链接...
python scripts/docs/obsidian_sync.py --validate

REM 确认是否继续
set /p response="是否继续构建和部署网站？[y/N] "
if /i not "%response%"=="y" (
    echo 操作已取消
    exit /b 0
)

REM 生成侧边栏配置
echo 正在生成侧边栏配置...
python scripts/docs/obsidian_sync.py --sidebar --output website/sidebars.json

REM 构建网站
echo 正在构建Docusaurus网站...
cd website
call npm run build

REM 询问是否部署
set /p deploy_response="网站构建完成。是否要部署到GitHub Pages？[y/N] "
if /i "%deploy_response%"=="y" (
    echo 正在部署到GitHub Pages...
    call npm run deploy
    echo 部署完成！
) else (
    echo 网站构建已完成，但未部署。
    echo 构建结果位于: website/build
)

pause
