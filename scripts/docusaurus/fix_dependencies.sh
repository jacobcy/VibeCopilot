#!/bin/bash
# 修复Docusaurus依赖问题的脚本
# 降级React版本从19到18，解决兼容性问题

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
WEBSITE_DIR="${PROJECT_ROOT}/website"

echo "==================================="
echo "  Docusaurus 依赖修复脚本"
echo "==================================="
echo "项目根目录: ${PROJECT_ROOT}"
echo "网站目录: ${WEBSITE_DIR}"
echo "-----------------------------------"

# 检查website目录是否存在
if [ ! -d "${WEBSITE_DIR}" ]; then
    echo "错误: 未找到website目录，确保Docusaurus已正确安装"
    exit 1
fi

# 直接进入website目录
cd "${WEBSITE_DIR}"
echo "已切换到website目录: $(pwd)"

# 备份原始package.json
echo "备份原始package.json..."
cp package.json package.json.bak

# 修改React版本
echo "将React版本从19降级到18..."
# 使用sed进行替换 (MacOS和Linux语法略有不同)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # MacOS
    sed -i '' 's/"react": "\^19.0.0"/"react": "\^18.0.0"/g' package.json
    sed -i '' 's/"react-dom": "\^19.0.0"/"react-dom": "\^18.0.0"/g' package.json
else
    # Linux
    sed -i 's/"react": "\^19.0.0"/"react": "\^18.0.0"/g' package.json
    sed -i 's/"react-dom": "\^19.0.0"/"react-dom": "\^18.0.0"/g' package.json
fi

echo "清理node_modules和缓存..."
rm -rf node_modules
rm -rf .docusaurus
npm cache clean --force

echo "重新安装依赖..."
npm install

echo "-----------------------------------"
echo "修复完成！"
echo "现在可以尝试运行: npm run start 或 npm run build"
