"""
模板初始数据模块

提供模板表的初始数据
"""

import logging
from datetime import datetime

from src.db import get_session
from src.db.repositories.template_repository import TemplateRepository

logger = logging.getLogger(__name__)


def init_templates():
    """初始化模板数据"""
    session = get_session()
    repo = TemplateRepository(session)

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
            "category": "frontend",
            "language": "typescript",
            "status": "active",
        }
    ]

    success_count = 0
    for template in templates:
        try:
            repo.create(**template)
            success_count += 1
        except Exception as e:
            logger.error(f"创建模板失败: {template['name']}", exc_info=True)

    logger.info(f"模板初始化完成: 成功 {success_count}/{len(templates)}")
    session.close()
