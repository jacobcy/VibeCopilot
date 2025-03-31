"""
模板管理器 - 管理文档模板和模板渲染.

提供创建新文档、应用模板和模板变量替换等功能.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class TemplateManager:
    """文档模板管理器，处理模板渲染和创建."""

    def __init__(self, template_dir: str):
        """
        初始化模板管理器.

        Args:
            template_dir: 模板目录路径
        """
        self.template_dir = Path(template_dir)
        self._ensure_default_templates()

    def list_templates(self) -> List[str]:
        """
        列出所有可用模板.

        Returns:
            模板名称列表
        """
        templates = []

        for file_path in self.template_dir.glob("*.md"):
            templates.append(file_path.stem)

        return templates

    def create_document(
        self, template_name: str, output_path: str, variables: Dict[str, Any] = None
    ) -> bool:
        """
        使用模板创建新文档.

        Args:
            template_name: 模板名称
            output_path: 输出文件路径
            variables: 模板变量字典

        Returns:
            创建是否成功
        """
        template_path = self.template_dir / f"{template_name}.md"

        if not template_path.exists():
            return False

        try:
            # 读取模板内容
            template_content = template_path.read_text(encoding="utf-8")

            # 渲染模板
            rendered_content = self._render_template(template_content, variables or {})

            # 确保输出目录存在
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 写入渲染后的内容
            output_file.write_text(rendered_content, encoding="utf-8")

            return True

        except Exception as e:
            print(f"创建文档失败: {str(e)}")
            return False

    def _render_template(self, content: str, variables: Dict[str, Any]) -> str:
        """
        渲染模板内容.

        Args:
            content: 模板内容
            variables: 模板变量

        Returns:
            渲染后的内容
        """
        # 添加默认变量
        all_vars = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "year": datetime.now().year,
        }

        # 合并用户提供的变量
        all_vars.update(variables)

        # 替换模板变量 {{var}}
        pattern = r"{{([^}]+)}}"

        def replace_var(match):
            var_name = match.group(1).strip()

            if var_name in all_vars:
                value = all_vars[var_name]
                # 确保值是字符串
                return str(value)

            # 如果变量不存在，保留原样
            return match.group(0)

        return re.sub(pattern, replace_var, content)

    def _ensure_default_templates(self):
        """确保默认模板存在."""
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # 创建默认文档模板
        self._create_default_template(
            "default",
            """---
title: {{title}}
description: {{description}}
category: {{category}}
created: {{date}}
updated: {{date}}
---

# {{title}}

## 概述

{{description}}

## 内容

## 相关文档

## 参考资料
""",
        )

        # 创建API文档模板
        self._create_default_template(
            "api",
            """---
title: {{title}} API
description: {{description}}
category: API文档
created: {{date}}
updated: {{date}}
---

# {{title}} API

## 概述

{{description}}

## API参考

### 接口

```typescript
interface {{name}} {
  // TODO: 添加接口定义
}
```

### 方法

#### method()

```typescript
function method(param: string): void
```

**参数:**
- `param` - 参数描述

**返回值:**
- 返回值描述

**示例:**

```typescript
// 用法示例
```

## 错误处理

## 最佳实践

## 相关API
""",
        )

        # 创建教程模板
        self._create_default_template(
            "tutorial",
            """---
title: {{title}} 教程
description: {{description}}
category: 教程
created: {{date}}
updated: {{date}}
---

# {{title}} 教程

## 简介

{{description}}

## 前提条件

- 前提条件1
- 前提条件2

## 步骤

### 步骤1: 开始

### 步骤2: 配置

### 步骤3: 运行

## 常见问题

## 进阶用法

## 相关资源
""",
        )

    def _create_default_template(self, name: str, content: str):
        """
        创建默认模板.

        Args:
            name: 模板名称
            content: 模板内容
        """
        template_path = self.template_dir / f"{name}.md"

        if not template_path.exists():
            template_path.write_text(content, encoding="utf-8")
