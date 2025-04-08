@echo off
REM 运行VibeCopilot测试的辅助脚本
REM 使用: scripts\run_tests.bat [模块路径]
REM 例子:
REM   scripts\run_tests.bat                 - 运行所有测试
REM   scripts\run_tests.bat db              - 运行数据库测试
REM   scripts\run_tests.bat validation      - 运行验证测试
REM   scripts\run_tests.bat cli\commands    - 运行特定目录下的测试

REM 切换到项目根目录
pushd %~dp0\..

echo === 开始 VibeCopilot 测试 ===
python --version
echo 当前目录: %CD%

IF "%~1"=="" (
    REM 如果没有指定模块，运行所有测试
    echo 运行所有测试...
    python -m pytest tests\ --tb=native -v
) ELSE (
    REM 运行指定模块的测试
    echo 运行 tests\%1 中的测试...
    python -m pytest tests\%1 --tb=native -v
)

REM 获取测试结果
IF %ERRORLEVEL% EQU 0 (
    echo 所有测试通过!
    popd
    exit /b 0
) ELSE (
    echo 测试失败!
    popd
    exit /b 1
)
