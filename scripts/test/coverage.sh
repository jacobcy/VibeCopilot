#!/bin/bash
# 生成测试覆盖率报告
# 使用: ./scripts/coverage.sh

set -e

# 确保我们在项目根目录
cd "$(dirname "$0")/.."

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示开始
echo -e "${BLUE}=== 生成 VibeCopilot 测试覆盖率报告 ===${NC}"
echo -e "${YELLOW}Python 版本:${NC} $(python --version)"
echo -e "${YELLOW}当前目录:${NC} $(pwd)"

# 创建覆盖率目录
mkdir -p coverage

# 运行测试并生成覆盖率报告
echo -e "${YELLOW}运行测试并生成覆盖率报告...${NC}"
python -m pytest --cov=src tests/ --cov-report=term --cov-report=html:coverage/html

# 获取结果
RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}覆盖率报告生成成功!${NC}"
    echo -e "${YELLOW}HTML报告位置:${NC} $(pwd)/coverage/html/index.html"

    # 尝试自动打开报告
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open coverage/html/index.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v xdg-open &> /dev/null; then
            xdg-open coverage/html/index.html
        fi
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        start coverage/html/index.html
    fi

    exit 0
else
    echo -e "${RED}测试覆盖率报告生成失败!${NC}"
    exit 1
fi
