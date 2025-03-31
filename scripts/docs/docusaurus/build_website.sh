#!/bin/bash
# 专用脚本 - 仅构建Docusaurus网站，避免npm错误

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
WEBSITE_DIR="${PROJECT_ROOT}/website"

echo "==================================="
echo "  Docusaurus 网站构建脚本"
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

# 检查依赖是否已安装
if [ ! -d "node_modules" ]; then
    echo "正在安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "依赖安装失败，请检查Node.js版本和npm配置"
        exit 1
    fi
    echo "依赖安装完成"
fi

# 构建网站
echo "正在构建Docusaurus网站..."
npm run build
if [ $? -ne 0 ]; then
    echo "构建失败，请检查错误信息"
    exit 1
fi

echo "-----------------------------------"
echo "构建成功！"
echo "构建结果位于: ${WEBSITE_DIR}/build"
echo "-----------------------------------"
echo "如需部署网站，请运行: cd website && npm run deploy"
