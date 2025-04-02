"""
转换器常量和配置。
"""

# 定义不进行同步的文件模式
DEFAULT_EXCLUDE_PATTERNS = {
    # Docusaurus特定文件
    r".*_category_\.json$",
    r".*\.docusaurus/.*",
    r".*\.DS_Store$",
    # Obsidian配置文件
    r".*\.obsidian/app\.json$",
    r".*\.obsidian/appearance\.json$",
    r".*\.obsidian/core-plugins\.json$",
    r".*\.obsidian/workspace\.json$",
    r".*\.obsidian/workspace\.json\.bak$",
    r".*\.obsidian/plugins/.*",
    # 排除website目录下的Docusaurus生成文件
    r".*/website/docs/.*",
}
