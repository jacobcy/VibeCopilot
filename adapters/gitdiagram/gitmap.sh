#!/bin/bash
# GitMap - 项目结构分析与路线图生成工具
# 基于GitDiagram的集成工具

# 显示帮助信息
show_help() {
  echo "GitMap - 项目结构分析与路线图生成工具"
  echo ""
  echo "用法: gitmap [选项] [项目路径]"
  echo ""
  echo "选项:"
  echo "  -h, --help            显示此帮助信息"
  echo "  -o, --output DIR      指定输出目录，默认为.ai目录下的'gitmap_output'"
  echo "  -i, --instructions TEXT   自定义分析指令，如'突出显示数据流'"
  echo "  -k, --key KEY         指定OpenAI API密钥"
  echo "  -r, --refactor        重构模式，分析已有项目并更新路线图"
  echo ""
  echo "示例:"
  echo "  gitmap /path/to/project"
  echo "  gitmap -o ./diagrams -i '分析数据流' /path/to/project"
  echo "  gitmap -r /path/to/refactored/project"
}

# 默认参数
PROJECT_PATH=""
OUTPUT_DIR="./gitmap_output"
INSTRUCTIONS=""
OPENAI_KEY=""
REFACTOR_MODE=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      exit 0
      ;;
    -o|--output)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -i|--instructions)
      INSTRUCTIONS="$2"
      shift 2
      ;;
    -k|--key)
      OPENAI_KEY="$2"
      shift 2
      ;;
    -r|--refactor)
      REFACTOR_MODE=true
      shift
      ;;
    -*)
      echo "错误: 未知选项 $1"
      show_help
      exit 1
      ;;
    *)
      if [ -z "$PROJECT_PATH" ]; then
        PROJECT_PATH="$1"
      else
        echo "错误: 项目路径已指定为 '$PROJECT_PATH'，无法再次指定为 '$1'"
        exit 1
      fi
      shift
      ;;
  esac
done

# 检查项目路径是否提供
if [ -z "$PROJECT_PATH" ]; then
  echo "错误: 未指定项目路径"
  show_help
  exit 1
fi

# 检查项目路径是否存在
if [ ! -d "$PROJECT_PATH" ]; then
  echo "错误: 项目路径不存在或不是目录: $PROJECT_PATH"
  exit 1
fi

# 提取项目名称，用于文件命名
PROJECT_NAME=$(basename "$PROJECT_PATH")
if [ -z "$PROJECT_NAME" ]; then
  # 如果无法获取项目名称，使用随机生成的名称
  PROJECT_NAME="project_$(date +%s)"
fi

# 如果处于重构模式，调整指令
if [ "$REFACTOR_MODE" = true ]; then
  if [ -z "$INSTRUCTIONS" ]; then
    INSTRUCTIONS="这是一个已重构的项目，请分析其当前架构并突出显示关键组件和数据流，适合用于更新项目文档和路线图"
  fi
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 测试OpenAI API密钥
echo "检查环境变量和API密钥..."
if [ -f ".env" ]; then
  # 尝试运行测试脚本
  PYTHON_SCRIPT_PATH="$(dirname $0)/../basic_memory/test_openai_key.py"
  if [ -f "$PYTHON_SCRIPT_PATH" ]; then
    echo "正在测试OpenAI API密钥..."
    python "$PYTHON_SCRIPT_PATH"
    KEY_TEST_RESULT=$?
    if [ $KEY_TEST_RESULT -ne 0 ]; then
      echo "错误: OpenAI API密钥测试失败，请检查环境变量配置。"
      exit 1
    fi
  else
    echo "警告: 无法找到API密钥测试脚本，将继续但可能会失败。"
  fi
else
  echo "警告: 未找到.env文件，请确保您已配置OpenAI API密钥。"
  if [ -z "$OPENAI_API_KEY" ]; then
    echo "错误: 未检测到OPENAI_API_KEY环境变量，无法继续。"
    exit 1
  fi
fi

# 构建命令
CMD="python $(dirname "$0")/analyze.py --path \"$PROJECT_PATH\" --output \"$OUTPUT_DIR\""

if [ -n "$INSTRUCTIONS" ]; then
  CMD="$CMD --instructions \"$INSTRUCTIONS\""
fi

if [ -n "$OPENAI_KEY" ]; then
  CMD="$CMD --openai-key \"$OPENAI_KEY\""
fi

# 输出运行信息
echo "正在分析项目: $PROJECT_PATH"
echo "输出目录: $OUTPUT_DIR"
if [ -n "$INSTRUCTIONS" ]; then
  echo "自定义指令: $INSTRUCTIONS"
fi
if [ "$REFACTOR_MODE" = true ]; then
  echo "模式: 重构分析"
else
  echo "模式: 标准分析"
fi

# 执行分析脚本
eval $CMD

# 检查执行结果
if [ $? -eq 0 ]; then
  # 重命名输出文件为项目名称格式
  if [ -f "$OUTPUT_DIR/project_explanation.md" ]; then
    mv "$OUTPUT_DIR/project_explanation.md" "$OUTPUT_DIR/${PROJECT_NAME}_explanation.md"
  fi

  if [ -f "$OUTPUT_DIR/project_diagram.md" ]; then
    mv "$OUTPUT_DIR/project_diagram.md" "$OUTPUT_DIR/${PROJECT_NAME}_diagram.md"
  fi

  echo ""
  echo "分析完成! 📊"
  echo "结果文件:"
  echo "  - 项目解释: $OUTPUT_DIR/${PROJECT_NAME}_explanation.md"
  echo "  - 架构图: $OUTPUT_DIR/${PROJECT_NAME}_diagram.md"

  # 提示下一步操作
  echo ""
  echo "💡 提示: 您可以使用Markdown查看器查看生成的文件，"
  echo "   或将${PROJECT_NAME}_diagram.md中的图表代码粘贴到Mermaid在线编辑器进行查看和编辑。"
  echo "   Mermaid在线编辑器: https://mermaid.live"

  # 如果在VibeCopilot项目内，提供额外提示
  if [[ "$PROJECT_PATH" == *"VibeCopilot"* ]]; then
    echo ""
    echo "📝 VibeCopilot集成: 您可以将生成的架构图添加到开发文档中:"
    echo "   cp $OUTPUT_DIR/${PROJECT_NAME}_diagram.md ~/Public/VibeCopilot/docs/dev/architecture/"
  fi
else
  echo "分析过程中发生错误，请检查日志以获取详细信息。"
  exit 1
fi
