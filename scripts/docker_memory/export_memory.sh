#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# 确保在正确的Python环境中
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# 运行Python导出脚本
python3 "${SCRIPT_DIR}/export_memory_to_obsidian.py"

# 检查运行结果
if [ $? -eq 0 ]; then
    echo "✨ 导出完成！"
    echo "👉 请使用Obsidian打开目录: $PROJECT_ROOT/.ai/knowledge_graph"
else
    echo "❌ 导出失败，请检查错误信息"
    exit 1
fi
