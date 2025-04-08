#!/usr/bin/env python3
"""
模板数据库初始化

初始化模板系统相关的表格和示例数据。
使用项目统一的数据库初始化机制。
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml  # 导入yaml库确保正确解析Front Matter

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent.absolute()
sys.path.append(str(current_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 导入项目数据库管理模块
from src.models.db.init_db import get_db_path, init_db
from src.models.db.template import Template, TemplateVariable


def load_sample_template(session):
    """加载示例模板"""
    # 检查是否已存在示例模板
    existing = session.query(Template).filter_by(name="示例命令模板").first()
    if existing:
        logger.info("示例模板已存在，跳过导入")
        return

    # 创建示例模板
    sample_template = Template(
        name="示例命令模板",
        description="用于创建命令的基本模板",
        type="command",
        content="""
# {{name}} 命令

## 描述
{{description}}

## 用法
```
/{{command}} [参数]
```

## 参数
{% for param in parameters %}
- `{{param.name}}`: {{param.description}}{% if param.required %} (必填){% endif %}
{% endfor %}

## 示例
```
{{example}}
```

## 注意事项
{{notes}}
        """.strip(),
        example="/help - 显示帮助信息",
        author="System",
        version="1.0.0",
        tags=json.dumps(["command", "template", "system"]),
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    # 添加模板变量
    variables = [
        TemplateVariable(template=sample_template, name="name", type="string", description="命令的名称", default_value="help", required=True),
        TemplateVariable(template=sample_template, name="description", type="string", description="命令的详细描述", default_value="显示帮助信息", required=True),
        TemplateVariable(template=sample_template, name="command", type="string", description="命令的触发关键词", default_value="help", required=True),
        TemplateVariable(
            template=sample_template,
            name="parameters",
            type="array",
            description="命令的参数列表",
            default_value=json.dumps([{"name": "topic", "description": "帮助主题", "required": False}]),
            required=False,
        ),
        TemplateVariable(template=sample_template, name="example", type="string", description="命令用法示例", default_value="/help flows", required=True),
        TemplateVariable(
            template=sample_template, name="notes", type="string", description="使用命令时的注意事项", default_value="此命令可在任何上下文中使用", required=False
        ),
    ]

    # 保存到数据库
    session.add(sample_template)
    session.commit()
    logger.info("已成功导入示例模板")


def import_templates_from_directory(session, directory: str):
    """从目录导入模板"""
    template_dir = Path(directory)
    if not template_dir.exists():
        logger.warning(f"目录不存在: {directory}")
        return 0

    count = 0
    for file_path in template_dir.glob("**/*.md"):
        try:
            # 读取文件内容
            content = file_path.read_text(encoding="utf-8")

            # 提取Front Matter
            front_matter = {}
            content_parts = content.split("---", 2)
            raw_content = content

            if len(content_parts) >= 3:
                try:
                    front_matter_str = content_parts[1].strip()
                    # 直接提取键值对，不尝试解析Jinja2变量
                    front_matter = extract_front_matter(front_matter_str)
                    content = content_parts[2].strip()
                except Exception as e:
                    logger.error(f"解析Front Matter失败: {str(e)}")

            # 创建模板记录
            template = Template(
                name=front_matter.get("title", file_path.stem),
                description=front_matter.get("description", ""),
                type=front_matter.get("type", "general"),
                content=content,
                example=front_matter.get("example", ""),
                author=front_matter.get("author", "System"),
                version=front_matter.get("version", "1.0.0"),
                tags=json.dumps(front_matter.get("tags", [])),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )

            # 提取变量(简单实现)
            variables = []
            for var_name, var_info in front_matter.get("variables", {}).items():
                if isinstance(var_info, dict):
                    variable = TemplateVariable(
                        template=template,
                        name=var_name,
                        type=var_info.get("type", "string"),
                        description=var_info.get("description", ""),
                        default_value=json.dumps(var_info.get("default", "")) if var_info.get("default") else None,
                        required=var_info.get("required", True),
                        enum_values=json.dumps(var_info.get("enum", [])) if var_info.get("enum") else None,
                    )
                    variables.append(variable)

            # 保存到数据库
            session.add(template)
            session.commit()
            count += 1
            logger.info(f"已导入模板: {template.name}")
        except Exception as e:
            logger.error(f"导入模板失败 ({file_path}): {str(e)}")

    return count


def extract_front_matter(front_matter_str):
    """从原始Front Matter字符串提取键值对，忽略Jinja2模板变量解析"""
    result = {}

    # 逐行解析，避免YAML解析器报错
    lines = front_matter_str.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # 尝试提取键值对
        parts = line.split(":", 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()

            # 去除可能的引号
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            # 存储为原始字符串，不尝试解析JSON或其他格式
            result[key] = value

    return result


def initialize_templates():
    """初始化模板数据"""
    try:
        # 首先确保数据库已初始化
        logger.info("确保数据库已初始化...")
        if not init_db():
            logger.error("数据库初始化失败，无法继续导入模板")
            return False

        # 获取数据库路径
        db_path = get_db_path()
        database_url = f"sqlite:///{db_path}"

        # 创建会话
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        try:
            # 加载示例模板
            logger.info("加载示例模板...")
            load_sample_template(session)

            # 可选：从模板目录导入其他模板
            templates_dir = current_dir / "templates"
            if templates_dir.exists():
                logger.info(f"从目录 {templates_dir} 导入模板...")
                count = import_templates_from_directory(session, str(templates_dir))
                logger.info(f"共导入了 {count} 个模板")

            logger.info("模板数据初始化完成")
            return True
        finally:
            session.close()

    except Exception as e:
        logger.error(f"初始化模板数据失败: {str(e)}")
        return False


def main():
    """主函数"""
    try:
        import yaml
    except ImportError:
        logger.error("缺少yaml库，请安装: pip install pyyaml")
        return 1

    success = initialize_templates()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
