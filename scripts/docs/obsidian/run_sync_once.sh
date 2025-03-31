#!/bin/bash
# 一次性同步所有文档的脚本
# 这个脚本会执行一次完整的双向同步

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 激活虚拟环境（如果存在）
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 执行同步
echo "开始同步所有文档..."
python scripts/docs/obsidian_sync.py --sync-all

echo "同步完成。按任意键退出..."
read -n 1
