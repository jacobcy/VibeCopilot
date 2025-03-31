@echo off
REM 专用脚本 - 仅构建Docusaurus网站，避免npm错误

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..\..
set WEBSITE_DIR=%PROJECT_ROOT%\website

echo ===================================
echo   Docusaurus 网站构建脚本
echo ===================================
echo 项目根目录: %PROJECT_ROOT%
echo 网站目录: %WEBSITE_DIR%
echo -----------------------------------

REM 检查website目录是否存在
if not exist "%WEBSITE_DIR%" (
    echo 错误: 未找到website目录，确保Docusaurus已正确安装
    exit /b 1
)

REM 直接进入website目录
cd /d "%WEBSITE_DIR%"
echo 已切换到website目录: %CD%

REM 检查依赖是否已安装
if not exist node_modules (
    echo 正在安装依赖...
    call npm install
    if errorlevel 1 (
        echo 依赖安装失败，请检查Node.js版本和npm配置
        exit /b 1
    )
    echo 依赖安装完成
)

REM 构建网站
echo 正在构建Docusaurus网站...
call npm run build
if errorlevel 1 (
    echo 构建失败，请检查错误信息
    exit /b 1
)

echo -----------------------------------
echo 构建成功！
echo 构建结果位于: %WEBSITE_DIR%\build
echo -----------------------------------
echo 如需部署网站，请运行: cd website ^&^& npm run deploy

pause
