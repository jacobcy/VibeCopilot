#!/bin/bash
# VibeCopilot Memory服务测试运行脚本
# 此脚本运行所有memory相关测试，确保它们使用MemoryService统一封装

echo "===== VibeCopilot Memory服务测试 ====="
echo

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
RESET='\033[0m'

# 项目根目录
ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
TEST_DIR="$ROOT_DIR/test/memory_test"

echo -e "${BLUE}项目根目录:${RESET} $ROOT_DIR"
echo -e "${BLUE}测试目录:${RESET} $TEST_DIR"
echo

# 设置Python路径
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"

# 运行接口一致性测试
echo -e "${YELLOW}1. 运行MemoryService接口一致性测试${RESET}"
export PYTHONPATH=$ROOT_DIR:$PYTHONPATH
python "$TEST_DIR/test_memory_service.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}接口一致性测试失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}接口一致性测试通过${RESET}"
echo

# 运行命令测试
echo -e "${YELLOW}2. 运行Memory命令测试${RESET}"
python "$TEST_DIR/test_memory_cmd.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}命令测试失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}命令测试通过${RESET}"
echo

# 运行快速功能测试
echo -e "${YELLOW}3. 运行快速功能测试${RESET}"
"$TEST_DIR/quick_test.sh"
if [ $? -ne 0 ]; then
    echo -e "${RED}快速功能测试失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}快速功能测试通过${RESET}"
echo

# 运行标准遵循测试
echo -e "${YELLOW}4. 运行标准遵循测试${RESET}"
python "$TEST_DIR/permalink_test.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}标准遵循测试失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}标准遵循测试通过${RESET}"
echo

# 运行责任分离测试
echo -e "${YELLOW}5. 运行责任分离测试${RESET}"
python "$TEST_DIR/test_sync_separation.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}责任分离测试失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}责任分离测试通过${RESET}"
echo

# 运行性能测试
echo -e "${YELLOW}6. 运行性能测试${RESET}"
python "$TEST_DIR/performance_test.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}性能测试失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}性能测试通过${RESET}"
echo

echo -e "${GREEN}所有测试通过!${RESET}"
echo -e "${BLUE}注意:${RESET} 所有测试均已使用MemoryService统一封装"
echo

echo "===== 测试报告 ====="
echo "1. 接口一致性: ✅ 通过"
echo "2. 命令行接口: ✅ 通过"
echo "3. 功能完整性: ✅ 通过"
echo "4. 标准遵循: ✅ 通过"
echo "5. 责任分离: ✅ 通过"
echo "6. 性能指标: ✅ 通过"

# 提供手动测试选项
echo
echo -e "${YELLOW}是否要运行手动测试?${RESET} (y/N)"
read -r run_manual

if [[ "$run_manual" == "y" || "$run_manual" == "Y" ]]; then
    "$TEST_DIR/manual_test.sh"
fi

echo
echo "测试完成"
