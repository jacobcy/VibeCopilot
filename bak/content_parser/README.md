# 内容解析器 (Content Parser)

内容解析器是一个处理、解析不同类型内容的组件，可以从Markdown文档中解析结构化数据，支持规则(Rule)、文档(Document)和通用内容(Generic)的解析。

## 架构

内容解析器采用了模块化设计，主要组件包括：

1. **统一入口** - `ContentParser`类：提供统一的接口，自动选择合适的解析器
2. **基础抽象类** - 定义解析器的基本接口和共用方法
   - `BaseAPIClient` - API客户端基类
   - `BaseContentParser` - 内容解析器基类
   - `ParsingMixin` - 解析辅助方法
3. **解析器实现** - 不同后端的具体实现
   - OpenAI实现 - 使用OpenAI API进行内容解析
   - (未来可扩展其他实现)
4. **工具类** - 提供各种辅助功能
   - 内容模板 - 提供默认结构和验证方法
   - 解析Mixin - 提供针对特定内容类型的解析方法

## 主要组件说明

### 1. 统一入口 (ContentParser)

```python
from adapters.content_parser import ContentParser

# 创建解析器实例
parser = ContentParser(model="gpt-4o-mini")

# 解析文件
result = parser.parse_file("path/to/file.md")

# 解析文本内容
result = parser.parse_content("# 文档标题\n内容...", content_type="document")

# 解析整个目录
results = parser.parse_directory("path/to/directory", pattern="*.md")
```

### 2. 解析器实现

#### OpenAI解析器

使用OpenAI API进行内容解析，支持三种内容类型：

- **规则解析器** (`OpenAIRuleParser`) - 解析规则文档，提取规则项、示例等
- **文档解析器** (`OpenAIDocumentParser`) - 解析文档内容，提取标题、描述和内容块
- **通用解析器** (`OpenAIGenericParser`) - 解析通用内容，提取关键点和摘要

每个解析器都会：

1. 优先使用API进行解析
2. 如果API失败，回退到本地解析方法
3. 添加必要的元数据和上下文信息

### 3. 解析结果格式

#### 规则(Rule)解析结果

```json
{
  "id": "rule-id",
  "title": "规则标题",
  "description": "规则描述",
  "type": "manual",
  "items": [
    {
      "content": "规则项内容",
      "priority": 1,
      "category": "general"
    }
  ],
  "examples": [
    {
      "content": "示例内容",
      "is_valid": true
    }
  ],
  "globs": ["*.md"],
  "always_apply": false
}
```

#### 文档(Document)解析结果

```json
{
  "id": "doc-id",
  "title": "文档标题",
  "description": "文档描述",
  "blocks": [
    {
      "type": "heading",
      "content": "标题内容",
      "level": 1
    },
    {
      "type": "paragraph",
      "content": "段落内容"
    },
    {
      "type": "code",
      "content": "代码内容",
      "language": "python"
    }
  ]
}
```

#### 通用(Generic)解析结果

```json
{
  "id": "generic-id",
  "title": "内容标题",
  "description": "内容描述",
  "type": "generic",
  "key_points": ["关键点1", "关键点2"],
  "summary": "内容摘要..."
}
```

## 扩展指南

### 添加新的解析器实现

1. 创建新的API客户端，继承`BaseAPIClient`
2. 创建新的内容解析器，继承`BaseContentParser`
3. 实现特定类型的解析器(规则、文档、通用)
4. 在`ContentParser`中注册新的解析器

## 版本历史

- **v1.0.0** (2024-04-06)
  - 首次发布
  - 支持OpenAI后端
  - 支持规则、文档和通用内容解析
