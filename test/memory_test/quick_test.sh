#!/bin/bash
# VibeCopilot Memory快速功能测试脚本

echo "===== 开始快速功能测试 ====="

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
RESET='\033[0m'

# 项目根目录
ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
TEST_DIR="$ROOT_DIR/test/memory_test"

# 设置Python路径
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"

# 创建临时测试文件夹和文件
TEST_FOLDER="quick_test_folder"
TEST_TITLE="quick_test_note"
TEST_CONTENT="这是一个快速测试内容"

echo -e "${YELLOW}1. 测试创建笔记${RESET}"
vibecopilot memory create --title "$TEST_TITLE" --folder "$TEST_FOLDER" --content "$TEST_CONTENT" --tags "测试,快速测试"
if [ $? -ne 0 ]; then
    echo -e "${RED}创建笔记失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}创建笔记成功${RESET}"
echo

echo -e "${YELLOW}2. 测试读取笔记${RESET}"
vibecopilot memory show --path "$TEST_FOLDER/$TEST_TITLE"
if [ $? -ne 0 ]; then
    echo -e "${RED}读取笔记失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}读取笔记成功${RESET}"
echo

echo -e "${YELLOW}3. 测试更新笔记${RESET}"
vibecopilot memory update --path "$TEST_FOLDER/$TEST_TITLE" --content "$TEST_CONTENT - 已更新"
if [ $? -ne 0 ]; then
    echo -e "${RED}更新笔记失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}更新笔记成功${RESET}"
echo

echo -e "${YELLOW}4. 测试搜索笔记${RESET}"
vibecopilot memory search --query "快速测试"
if [ $? -ne 0 ]; then
    echo -e "${RED}搜索笔记失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}搜索笔记成功${RESET}"
echo

echo -e "${YELLOW}5. 测试列出笔记${RESET}"
vibecopilot memory list --folder "$TEST_FOLDER"
if [ $? -ne 0 ]; then
    echo -e "${RED}列出笔记失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}列出笔记成功${RESET}"
echo

echo -e "${YELLOW}6. 清理测试笔记${RESET}"
vibecopilot memory delete --path "$TEST_FOLDER/$TEST_TITLE" --force
if [ $? -ne 0 ]; then
    echo -e "${RED}删除笔记失败!${RESET}"
    exit 1
fi
echo -e "${GREEN}删除笔记成功${RESET}"
echo

echo -e "${GREEN}快速功能测试全部通过!${RESET}"
echo "===== 快速功能测试结束 ====="
exit 0
