#!/bin/bash
# 运行VibeCopilot测试的辅助脚本
# 使用: ./scripts/run_tests.sh [模块路径]
# 例子:
#   ./scripts/run_tests.sh                 - 运行所有测试
#   ./scripts/run_tests.sh db              - 运行数据库测试
#   ./scripts/run_tests.sh validation      - 运行验证测试
#   ./scripts/run_tests.sh cli/commands    - 运行特定目录下的测试

set -e

# 确保我们在项目根目录
cd "$(dirname "$0")/.."

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示测试开始
echo -e "${BLUE}=== 开始 VibeCopilot 测试 ===${NC}"
echo -e "${YELLOW}Python 版本:${NC} $(python --version)"
echo -e "${YELLOW}当前目录:${NC} $(pwd)"

if [ -z "$1" ]; then
    # 如果没有指定模块，运行所有测试
    echo -e "${YELLOW}运行所有测试...${NC}"
    python -m pytest tests/ --tb=native -v
else
    # 运行指定模块的测试
    echo -e "${YELLOW}运行 tests/$1 中的测试...${NC}"
    python -m pytest tests/$1 --tb=native -v
fi

# 获取测试结果
TEST_RESULT=$?

# 根据测试结果显示信息
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}所有测试通过!${NC}"
    exit 0
else
    echo -e "${RED}测试失败!${NC}"
    exit 1
fi
