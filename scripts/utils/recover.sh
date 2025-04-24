#!/bin/bash

# 设置路径
RECOVER_SRC="/Volumes/Cube/recovered"  # 恢复工具输出路径
DEST="/Volumes/Cube/vibe-backup"

# 创建目标目录结构
mkdir -p "$DEST"/{python,toml,json,markdown,yaml,other}

echo "🔍 开始筛选恢复文件中与 VibeCopilot 项目相关的内容..."

# 搜索 .py 文件
find "$RECOVER_SRC" -iname "*.py" -exec grep -qi 'vibe' {} \; -exec cp {} "$DEST/python/" \;

# 搜索 .toml 文件
find "$RECOVER_SRC" -iname "*.toml" -exec grep -qi 'vibe' {} \; -exec cp {} "$DEST/toml/" \;

# 搜索 .json 文件
find "$RECOVER_SRC" -iname "*.json" -exec grep -qi 'vibe' {} \; -exec cp {} "$DEST/json/" \;

# 搜索 .md 文件
find "$RECOVER_SRC" -iname "*.md" -exec grep -qi 'vibe' {} \; -exec cp {} "$DEST/markdown/" \;

# 搜索 .yaml 和 .yml 文件
find "$RECOVER_SRC" \( -iname "*.yaml" -o -iname "*.yml" \) -exec grep -qi 'vibe' {} \; -exec cp {} "$DEST/yaml/" \;

# 其他可能的文件（.txt等）
find "$RECOVER_SRC" -type f ! -iname ".*" -exec grep -qi 'vibe' {} \; -exec cp {} "$DEST/other/" \;

echo "✅ 筛选完成，所有文件已复制至：$DEST"
