"""
模板初始数据模块

提供模板表的初始数据
"""

import json
import logging
from datetime import datetime

from src.db import get_session
from src.db.repositories.template_repository import TemplateRepository

logger = logging.getLogger(__name__)


def init_templates():
    """初始化模板数据"""
    session = get_session()
    # Initialize repo without session
    repo = TemplateRepository()

    # 添加一些示例模板
    templates = [
        {
            "name": "组件模板",
            "description": "React组件基础模板",
            "content": """
import React from 'react';

interface {{ComponentName}}Props {
  // 在此定义组件属性
}

export const {{ComponentName}}: React.FC<{{ComponentName}}Props> = (props) => {
  return (
    <div>
      {/* 在此实现组件内容 */}
    </div>
  );
};
""",
            "type": "frontend",
            "example": "// 使用示例\n<MyComponent prop1={value1} />",
            "author": "system",
            "version": "1.0.0",
            "tags": json.dumps(["react", "component", "typescript"]),
        }
    ]

    success_count = 0
    for template in templates:
        try:
            # Pass session to create method
            repo.create(session, data=template)
            success_count += 1
        except Exception as e:
            logger.error(f"创建模板失败: {template['name']}", exc_info=True)

    logger.info(f"模板初始化完成: 成功 {success_count}/{len(templates)}")
    session.close()
