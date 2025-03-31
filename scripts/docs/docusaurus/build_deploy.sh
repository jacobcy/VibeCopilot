#!/bin/bash
# 构建和部署Docusaurus网站的脚本

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

# 同步所有文档
echo "正在同步文档..."
python scripts/docs/obsidian_sync.py --sync-all

# 验证链接
echo "验证文档链接..."
python scripts/docs/obsidian_sync.py --validate

# 确认是否继续
read -p "是否继续构建和部署网站？[y/N] " response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 0
fi

# 生成侧边栏配置
echo "正在生成侧边栏配置..."
python scripts/docs/obsidian_sync.py --sidebar --output website/sidebars.json

# 构建网站
echo "正在构建Docusaurus网站..."
cd website
npm run build

# 询问是否部署
read -p "网站构建完成。是否要部署到GitHub Pages？[y/N] " deploy_response
if [[ "$deploy_response" =~ ^[Yy]$ ]]; then
    echo "正在部署到GitHub Pages..."
    npm run deploy
    echo "部署完成！"
else
    echo "网站构建已完成，但未部署。"
    echo "构建结果位于: website/build"
fi
