#!/bin/bash
# 同步项目文档到Obsidian的脚本
# 这个脚本会启动自动监控模式，实时同步项目文档到Obsidian

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 激活虚拟环境（如果存在）
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 启动同步监控
echo "正在启动文档同步监控..."
python scripts/docs/obsidian/sync.py --watch

# 如果用户按下Ctrl+C，优雅退出
trap "echo '停止监控'; exit 0" SIGINT SIGTERM

# 保持脚本运行
while true; do
    sleep 1
done
