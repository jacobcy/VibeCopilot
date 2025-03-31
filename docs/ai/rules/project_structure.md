# VibeCopilot 项目结构规范

## 标准目录结构

VibeCopilot项目采用以下标准化目录结构，所有代码开发必须遵循此结构：

```
/VibeCopilot
├── .cursor               # Cursor AI配置
│   └── rules             # AI行动规则
├── docs                  # 项目文档
│   ├── ai                # AI读取的文档
│   │   ├── rules         # AI行为规则
│   │   ├── templates     # 文档模板
│   │   └── prompts       # 提示词模板
│   ├── human             # 人类阅读的文档
│   │   ├── guides        # 使用指南
│   │   ├── tutorials     # 教程
│   │   └── references    # 参考资料
│   └── project           # 项目文档
│       ├── requirements  # 需求文档
│       ├── design        # 设计文档
│       └── roadmap       # 开发路线图
├── scripts               # 工具脚本
│   ├── setup             # 环境设置脚本
│   ├── github            # GitHub相关工具
│   ├── project           # 项目管理工具
│   └── utils             # 通用工具函数
├── tools                 # 集成工具
│   ├── github            # GitHub工具指南
│   ├── cursor            # Cursor工具指南
│   └── common            # 通用工具指南
├── templates             # 项目模板
│   ├── python            # Python项目模板
│   ├── nodejs            # Node.js项目模板
│   └── web               # Web项目模板
├── src                   # 源代码
│   ├── core              # 核心功能模块
│   ├── ui                # 用户界面相关
│   ├── services          # 服务层
│   └── utils             # 实用工具
└── tests                 # 测试代码
    ├── unit              # 单元测试
    └── integration       # 集成测试
```

## 文件命名约定

1. 所有文件名使用小写字母，单词之间使用下划线连接 (snake_case)
2. 目录名使用小写字母，单词之间使用下划线连接
3. Python 模块采用单数形式命名
4. 测试文件以 `test_` 前缀命名
5. 脚本文件应具有描述性名称，明确说明其功能

## 模块结构

1. 每个Python模块必须包含 `__init__.py` 文件
2. 模块内部结构遵循以下顺序:
   - 导入语句 (标准库 -> 第三方库 -> 本地模块)
   - 常量定义
   - 类定义
   - 函数定义
   - 主函数 (`if __name__ == "__main__":`)

## 文档规范

1. AI专用文档存放在 `/docs/ai/` 目录
2. 人类阅读文档存放在 `/docs/human/` 目录
3. 项目文档必须保持更新，与代码同步
4. 所有文档使用Markdown格式编写

## 代码组织原则

1. 相关功能应放在同一模块下
2. 避免循环导入
3. 每个脚本只处理一个主要功能
4. 共享功能提取到工具模块中
5. 配置与代码分离

在开发过程中，必须严格遵守此结构规范，确保项目结构清晰，便于维护和扩展。
