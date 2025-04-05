# CDDRG Engine

CDDRG（Context-Driven Dynamic Rule Generation）是一个上下文驱动的动态规则生成引擎，专为大语言模型应用设计。它基于上下文智能生成规则，并通过知识检索增强模型能力。

## 特性

- 上下文感知规则生成
- 灵活的知识库接入
- 高性能嵌入和检索
- 多模型适配器支持
- 评估与指标分析

## 安装

```bash
pip install cddrg_engine
```

## 快速开始

```python
from cddrg_engine import Engine
from cddrg_engine.config import EngineConfig

# 初始化引擎
config = EngineConfig(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    vector_store_path="./vector_store",
    model_adapter="openai"
)

engine = Engine(config)

# 添加知识
engine.add_knowledge(
    content="规则应当简洁明了，避免冗余",
    metadata={"type": "rule", "category": "style"}
)

# 生成规则
rule = engine.generate_rule(
    context="用户在编写代码文档",
    task="提供文档编写建议"
)

print(rule)
```

## 开发设置

```bash
# 克隆仓库
git clone https://github.com/jacobcy/VibeCopilot.git
cd VibeCopilot/cddrg_engine

# 使用uv创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装开发依赖
uv pip install -e ".[dev]"

# 运行测试
pytest
```

## 许可

MIT
