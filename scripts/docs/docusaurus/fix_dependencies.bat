@echo off
REM 修复Docusaurus依赖问题的脚本
REM 降级React版本从19到18，解决兼容性问题

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..\..
set WEBSITE_DIR=%PROJECT_ROOT%\website

echo ===================================
echo   Docusaurus 依赖修复脚本
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

REM 备份原始package.json
echo 备份原始package.json...
copy package.json package.json.bak

REM 需要使用PowerShell来替换文件内容
echo 将React版本从19降级到18...
powershell -Command "(Get-Content package.json) -replace '\"react\": \"\^19\.0\.0\"', '\"react\": \"\^18\.0\.0\"' | Set-Content package.json"
powershell -Command "(Get-Content package.json) -replace '\"react-dom\": \"\^19\.0\.0\"', '\"react-dom\": \"\^18\.0\.0\"' | Set-Content package.json"

echo 清理node_modules和缓存...
rmdir /s /q node_modules
rmdir /s /q .docusaurus
call npm cache clean --force

echo 重新安装依赖...
call npm install

echo -----------------------------------
echo 修复完成！
echo 现在可以尝试运行: npm run start 或 npm run build

pause
