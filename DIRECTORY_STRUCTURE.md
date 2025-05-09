# VibeCopilot Directory Structure

## Core Directories

```
VibeCopilot/
├── src/                    # 核心源代码目录
│   ├── api/               # API接口定义
│   ├── components/        # React组件
│   ├── services/          # 业务服务层
│   ├── models/           # 数据模型
│   └── utils/            # 通用工具函数
├── tests/                  # 测试代码目录
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── e2e/              # 端到端测试
├── config/                 # 配置文件目录
│   ├── default/          # 默认配置
│   ├── development/      # 开发环境配置
│   └── production/       # 生产环境配置
├── docs/                   # 文档目录
│   ├── api/              # API文档
│   ├── guides/           # 使用指南
│   └── architecture/     # 架构文档
├── scripts/                # 脚本工具目录
├── website/                # 文档网站
├── .ai/                    # AI相关资源
│   ├── memory/           # AI记忆存储
│   ├── prompts/          # 提示词模板
│   └── rules/            # AI规则定义
├── .cursor/                # Cursor IDE配置
├── .github/                # GitHub相关配置
└── data/                   # 数据存储目录
    ├── db/               # 数据库文件
    └── vectors/          # 向量数据库
```

## Supporting Directories

```
VibeCopilot/
├── adapters/               # 适配器实现
├── examples/               # 示例代码
├── templates/              # 项目模板
├── bin/                    # 可执行文件
└── modules/                # 扩展模块
```

## Development Directories

```
VibeCopilot/
├── .venv/                  # Python虚拟环境
├── node_modules/           # Node.js依赖
├── logs/                   # 日志文件
└── temp/                   # 临时文件
```

## Configuration Files

```
VibeCopilot/
├── pyproject.toml         # Python项目配置
├── setup.py              # Python安装配置
├── requirements.txt      # Python依赖
├── package.json          # Node.js项目配置
├── tsconfig.json         # TypeScript配置
├── .env                  # 环境变量
├── .flake8              # Python代码风格
├── .npmrc               # npm配置
├── .gitignore           # Git忽略文件
└── pytest.ini           # 测试配置
```

## Documentation Files

```
VibeCopilot/
├── README.md             # 项目说明
├── CHANGELOG.md          # 变更日志
├── CONTRIBUTING.md       # 贡献指南
└── LICENSE              # 许可证
```
