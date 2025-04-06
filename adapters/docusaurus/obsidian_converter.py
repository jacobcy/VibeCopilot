#!/usr/bin/env python
"""
Obsidian到Docusaurus转换工具

这个脚本基于Obsidiosaurus项目，提供了将Obsidian格式的Markdown文件转换为
Docusaurus格式的功能。它处理链接转换、图片处理等任务。

此文件为兼容性封装，实际实现已移至converter包
"""

import sys

from adapters.docusaurus.converter import ObsidianDocusaurusConverter, main

# 保留原始类名以保证向后兼容
ObsidianDocusaurusConverter = ObsidianDocusaurusConverter


if __name__ == "__main__":
    sys.exit(main())
