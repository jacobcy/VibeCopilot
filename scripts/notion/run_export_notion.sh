#!/bin/bash

# 设置颜色输出
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# 检查是否安装了ts-node
if ! command -v ts-node &> /dev/null
then
    echo -e "${RED}错误: ts-node未安装，请先安装: npm install -g ts-node typescript${NC}"
    exit 1
fi

# 检查脚本文件是否存在
SCRIPT_DIR="scripts/notion_to_md"
RUN_SCRIPT="$SCRIPT_DIR/run.js"
if [ ! -f "$RUN_SCRIPT" ]; then
    echo -e "${RED}错误: 找不到脚本文件 $RUN_SCRIPT${NC}"
    exit 1
fi

# 检查环境变量配置文件是否存在
ENV_FILE="config/default/.env.notion"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}警告: 找不到环境变量配置文件 $ENV_FILE${NC}"
    echo -e "${BLUE}创建示例配置文件 $ENV_FILE.example 供参考${NC}"

    # 如果示例文件不存在，创建一个
    EXAMPLE_FILE="config/default/.env.notion.example"
    if [ ! -f "$EXAMPLE_FILE" ]; then
        cat > "$EXAMPLE_FILE" << EOF
# Notion Export Configuration

# Notion API Key (必填)
# 从 https://www.notion.so/my-integrations 获取
NOTION_API_KEY=your_notion_api_key_here

# Notion Page ID (必填)
# 页面URL中的32位字符串，例如：https://www.notion.so/myworkspace/Page-Title-abcd1234abcd1234abcd1234abcd1234
# 只需要提取 abcd1234abcd1234abcd1234abcd1234 部分
NOTION_PAGE_ID=your_notion_page_id_here

# 输出文件名 (可选，默认为 exported_notion_page.md)
OUTPUT_FILENAME=notion_export.md

# 输出目录 (可选，默认为 exports)
OUTPUT_DIR=exports
EOF
    fi

    echo -e "${YELLOW}请先配置 $ENV_FILE 文件，参考 $ENV_FILE.example${NC}"
    echo -e "${BLUE}配置示例:${NC}"
    echo -e "${BLUE}NOTION_API_KEY=your_notion_api_key_here${NC}"
    echo -e "${BLUE}NOTION_PAGE_ID=your_notion_page_id_here${NC}"
    echo -e "${BLUE}OUTPUT_FILENAME=notion_export.md${NC}"
    echo -e "${BLUE}OUTPUT_DIR=exports${NC}"
    exit 1
fi

# 处理命令行参数
RECURSIVE_FLAG=""
MAX_DEPTH_VALUE=""
USE_TITLE_FLAG=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --recursive)
      RECURSIVE_FLAG="RECURSIVE=true"
      shift
      ;;
    --max-depth=*)
      MAX_DEPTH_VALUE="MAX_DEPTH=${1#*=}"
      shift
      ;;
    --use-title)
      USE_TITLE_FLAG="USE_PAGE_TITLE_AS_FILENAME=true"
      shift
      ;;
    --help)
      echo -e "${BLUE}用法: $0 [选项]${NC}"
      echo -e "${BLUE}选项:${NC}"
      echo -e "  ${BLUE}--recursive${NC}       递归导出所有子页面"
      echo -e "  ${BLUE}--max-depth=N${NC}    设置递归导出的最大深度（默认为无限制）"
      echo -e "  ${BLUE}--use-title${NC}      使用页面标题作为文件名"
      echo -e "  ${BLUE}--help${NC}           显示帮助信息"
      exit 0
      ;;
    *)
      echo -e "${RED}未知选项: $1${NC}"
      echo -e "${BLUE}使用 $0 --help 查看帮助信息${NC}"
      exit 1
      ;;
  esac
done

# 执行TypeScript脚本，加载环境变量
echo -e "${GREEN}开始执行Notion导出脚本...${NC}"

# 如果指定了命令行参数，优先使用命令行参数
if [ -n "$RECURSIVE_FLAG" ] || [ -n "$MAX_DEPTH_VALUE" ] || [ -n "$USE_TITLE_FLAG" ]; then
  echo -e "${BLUE}使用命令行参数覆盖配置文件设置${NC}"
  env $(cat "$ENV_FILE" | grep -v '^#' | xargs) $RECURSIVE_FLAG $MAX_DEPTH_VALUE $USE_TITLE_FLAG node $RUN_SCRIPT --recursive
else
  env $(cat "$ENV_FILE" | grep -v '^#' | xargs) node $RUN_SCRIPT
fi

# 检查执行结果
if [ $? -eq 0 ]; then
    echo -e "${GREEN}脚本执行成功!${NC}"
else
    echo -e "${RED}错误: 脚本执行失败${NC}"
    exit 1
fi
