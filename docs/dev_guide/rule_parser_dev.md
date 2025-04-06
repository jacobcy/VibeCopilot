# 规则解析系统开发指南

## 架构简述

规则解析系统采用模块化设计，通过解析器接口实现引擎无关的规则处理。系统主要组件包括：

```
adapters/rule_parser/
├── base_parser.py        # 解析器基类和接口定义
├── openai_rule_parser.py # OpenAI实现
├── ollama_rule_parser.py # Ollama实现
├── parser_factory.py     # 解析器工厂
├── utils.py              # 通用工具函数
├── main.py               # 命令行入口
└── lib/                  # 核心库
    ├── openai_api.py     # OpenAI API客户端
    ├── ollama_api.py     # Ollama API客户端
    ├── rule_template.py  # 规则模板和验证
    └── conflict_detector.py # 冲突检测
```

## 核心代码

### 解析器基类

`base_parser.py` 定义了解析器接口和基本功能：

```python
class BaseRuleParser(ABC):
    """规则解析器基类"""

    @abstractmethod
    def parse_rule(self, file_path: str) -> Dict[str, Any]:
        """解析规则文件"""
        pass

    @abstractmethod
    def detect_conflict(self, rule1: Dict[str, Any], rule2: Dict[str, Any]) -> Dict[str, Any]:
        """检测规则冲突"""
        pass
```

### 解析器实现

`openai_rule_parser.py` 实现了基于OpenAI的规则解析：

```python
class OpenAIRuleParser(BaseRuleParser):
    """使用OpenAI API实现的规则解析器"""

    def __init__(self, model=None):
        """初始化解析器"""
        self.client = OpenAIClient(model=model)

    def parse_rule(self, file_path: str) -> Dict[str, Any]:
        """解析规则文件"""
        # 读取文件内容
        # 构建提示词
        # 调用API解析
        # 验证响应
        # 返回结构化数据
```

### 环境变量加载

`main.py` 中实现了环境变量加载：

```python
def load_env():
    """加载环境变量"""
    env_path = find_env_file()
    load_dotenv(env_path)
    logger.info(f"从{env_path}加载环境变量")
```

## 注意事项

### API密钥和模型管理

系统通过环境变量管理API密钥和模型选择：

1. **敏感信息处理**：
   - API密钥存储在`.env`文件中，不应提交到版本控制
   - 默认使用OpenAI，但代码中不硬编码任何API密钥

2. **模型选择**：
   - 通过环境变量指定使用的模型
   - OpenAI和Ollama使用不同的环境变量控制

### 错误处理

系统实现了多层错误处理机制：

1. **API请求错误**：
   - 捕获API请求异常并提供详细日志
   - 支持重试机制和优雅降级

2. **解析错误**：
   - 验证API响应的合法性
   - 处理不符合预期的响应格式

3. **文件操作错误**：
   - 检查文件存在性
   - 处理读取错误和格式错误

## 技术债务

1. **OpenAI依赖**：
   - 系统主要依赖OpenAI进行高质量解析，Ollama作为备选但质量较低
   - 未来可考虑使用本地部署的大模型以降低API依赖

2. **解析质量**：
   - 复杂规则的解析准确性有待提升
   - 需要优化提示词工程以提高解析质量

3. **性能限制**：
   - API调用带来的延迟无法完全避免
   - 可能需要实现缓存机制以提高性能

4. **测试覆盖**：
   - 当前缺乏全面的单元测试
   - 需要增加更多测试用例以确保功能稳定性

## 扩展方向

1. **多引擎支持**：
   - 添加更多LLM引擎支持，如Claude、Gemini等
   - 实现引擎性能评估和自动选择机制

2. **规则验证增强**：
   - 添加更严格的规则结构验证
   - 支持自定义验证规则

3. **冲突检测优化**：
   - 实现更精细的冲突类型检测
   - 添加冲突解决建议功能

4. **批量处理能力**：
   - 支持批量规则解析和冲突检测
   - 实现并行处理以提高效率
