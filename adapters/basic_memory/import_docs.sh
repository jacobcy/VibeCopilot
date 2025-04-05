#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# 确保在正确的Python环境中
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# 检查参数
if [ "$#" -ne 1 ]; then
    echo "用法: $0 源目录"
    exit 1
fi

SOURCE_DIR="$1"

# 检查源目录是否存在
if [ ! -d "$SOURCE_DIR" ]; then
    echo "错误: 源目录不存在: $SOURCE_DIR"
    exit 1
fi

echo "源目录: $SOURCE_DIR"

# 运行Python导入脚本
python3 "${SCRIPT_DIR}/import_docs.py" "$SOURCE_DIR"

# 检查运行结果
if [ $? -eq 0 ]; then
    echo "✨ 开始同步到Basic Memory..."
    basic-memory sync
    echo "✨ 导入完成！"
else
    echo "❌ 导入失败，请检查错误信息"
    exit 1
fi
