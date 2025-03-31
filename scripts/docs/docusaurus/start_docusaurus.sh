#!/bin/bash
# 启动Docusaurus开发服务器的脚本
# 同时执行文档同步和Docusaurus服务器启动

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 激活虚拟环境（如果存在）
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 检查website目录是否存在
if [ ! -d "website" ]; then
    echo "错误: 未找到website目录，确保Docusaurus已正确安装"
    exit 1
fi

# 检查依赖是否已安装
if [ ! -d "website/node_modules" ]; then
    echo "安装Docusaurus依赖..."
    cd website
    npm install
    cd ..
fi

# 生成侧边栏配置
echo "正在生成侧边栏配置..."
python scripts/docs/obsidian/sync.py --sidebar --output website/sidebars.json

# 启动同步监控（后台运行）
echo "启动文档同步监控..."
python scripts/docs/obsidian/sync.py --watch &
SYNC_PID=$!

# 设置trap以在脚本退出时终止后台进程
trap "echo '停止所有进程'; kill $SYNC_PID 2>/dev/null; exit 0" SIGINT SIGTERM EXIT

# 启动Docusaurus开发服务器
echo "启动Docusaurus开发服务器..."
cd website
npm run start

# 如果Docusaurus服务器退出，也终止同步进程
kill $SYNC_PID 2>/dev/null
