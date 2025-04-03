---
title: 规则模板引擎API规范
created_at: 2025-04-03
status: approved
---

# 规则模板引擎API规范

## API概述

规则模板引擎API是一组RESTful接口，提供规则和模板的创建、读取、更新、删除及其他管理功能。API使用JSON作为数据交换格式，遵循标准HTTP方法和状态码。

## 基础URL

```
/api/v1
```

## 认证

所有API请求需要通过Bearer Token认证：

```
Authorization: Bearer <token>
```

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 10,
    "total": 100
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "details": { ... }
  }
}
```

## 规则管理API

### 获取规则列表

获取规则列表，支持分页、过滤和排序。

**请求**：

```
GET /rules
```

**查询参数**：

- `type`: 规则类型(agent|auto|manual|always)
- `tags`: 标签(逗号分隔)
- `search`: 搜索关键词
- `page`: 页码(默认1)
- `limit`: 每页数量(默认10)
- `sort`: 排序字段
- `order`: 排序方向(asc|desc)

**响应**：

```json
{
  "success": true,
  "data": [
    {
      "id": "rule-001",
      "name": "TypeScript最佳实践",
      "type": "agent",
      "description": "TypeScript开发的最佳实践规则",
      "globs": ["*.ts", "*.tsx"],
      "alwaysApply": false,
      "version": "1.0.0",
      "created_at": "2025-03-01T00:00:00Z",
      "updated_at": "2025-03-10T00:00:00Z",
      "metadata": {
        "author": "VibeCopilot Team",
        "tags": ["typescript", "best-practices"],
        "dependencies": [],
        "usage_count": 42,
        "effectiveness": 85
      }
    },
    ...
  ],
  "meta": {
    "page": 1,
    "limit": 10,
    "total": 42
  }
}
```

### 获取单个规则

根据ID获取单个规则的详细信息。

**请求**：

```
GET /rules/{id}
```

**路径参数**：

- `id`: 规则ID

**响应**：

```json
{
  "success": true,
  "data": {
    "id": "rule-001",
    "name": "TypeScript最佳实践",
    "type": "agent",
    "description": "TypeScript开发的最佳实践规则",
    "globs": ["*.ts", "*.tsx"],
    "alwaysApply": false,
    "content": "# TypeScript最佳实践\n\n## 关键规则\n\n- 使用类型注解...",
    "version": "1.0.0",
    "created_at": "2025-03-01T00:00:00Z",
    "updated_at": "2025-03-10T00:00:00Z",
    "metadata": {
      "author": "VibeCopilot Team",
      "tags": ["typescript", "best-practices"],
      "dependencies": [],
      "usage_count": 42,
      "effectiveness": 85
    }
  }
}
```

### 创建规则

创建新规则。

**请求**：

```
POST /rules
```

**请求体**：

```json
{
  "name": "React组件规则",
  "type": "agent",
  "description": "React组件开发的最佳实践",
  "globs": ["*.tsx", "src/components/**/*.ts"],
  "alwaysApply": false,
  "content": "# React组件规则\n\n## 关键规则\n\n- 组件应遵循单一职责原则...",
  "metadata": {
    "author": "VibeCopilot Team",
    "tags": ["react", "components"],
    "dependencies": ["rule-001"]
  }
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "id": "rule-002",
    "name": "React组件规则",
    "type": "agent",
    "description": "React组件开发的最佳实践",
    "globs": ["*.tsx", "src/components/**/*.ts"],
    "alwaysApply": false,
    "content": "# React组件规则\n\n## 关键规则\n\n- 组件应遵循单一职责原则...",
    "version": "1.0.0",
    "created_at": "2025-04-03T00:00:00Z",
    "updated_at": "2025-04-03T00:00:00Z",
    "metadata": {
      "author": "VibeCopilot Team",
      "tags": ["react", "components"],
      "dependencies": ["rule-001"],
      "usage_count": 0,
      "effectiveness": 0
    }
  }
}
```

### 更新规则

更新现有规则。

**请求**：

```
PUT /rules/{id}
```

**路径参数**：

- `id`: 规则ID

**请求体**：

```json
{
  "name": "React组件规则",
  "description": "React组件开发的最佳实践和模式",
  "globs": ["*.tsx", "src/components/**/*.ts", "src/pages/**/*.tsx"],
  "content": "# React组件规则\n\n## 关键规则\n\n- 组件应遵循单一职责原则...",
  "metadata": {
    "tags": ["react", "components", "patterns"]
  }
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "id": "rule-002",
    "name": "React组件规则",
    "type": "agent",
    "description": "React组件开发的最佳实践和模式",
    "globs": ["*.tsx", "src/components/**/*.ts", "src/pages/**/*.tsx"],
    "alwaysApply": false,
    "content": "# React组件规则\n\n## 关键规则\n\n- 组件应遵循单一职责原则...",
    "version": "1.1.0",
    "created_at": "2025-04-03T00:00:00Z",
    "updated_at": "2025-04-04T00:00:00Z",
    "metadata": {
      "author": "VibeCopilot Team",
      "tags": ["react", "components", "patterns"],
      "dependencies": ["rule-001"],
      "usage_count": 5,
      "effectiveness": 80
    }
  }
}
```

### 删除规则

删除规则。

**请求**：

```
DELETE /rules/{id}
```

**路径参数**：

- `id`: 规则ID

**响应**：

```json
{
  "success": true,
  "data": {
    "message": "规则已成功删除"
  }
}
```

### 验证规则

验证规则内容的格式和有效性。

**请求**：

```
POST /rules/validate
```

**请求体**：

```json
{
  "content": "# 规则标题\n\n## 关键规则\n\n- 规则1\n- 规则2\n\n## 示例\n\n<example>\n示例内容\n</example>"
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "valid": true,
    "issues": []
  }
}
```

或

```json
{
  "success": true,
  "data": {
    "valid": false,
    "issues": [
      {
        "line": 5,
        "message": "关键规则部分缺少具体内容"
      },
      {
        "line": 9,
        "message": "示例部分格式不正确"
      }
    ]
  }
}
```

### 获取推荐规则

基于当前上下文获取推荐规则。

**请求**：

```
POST /rules/recommend
```

**请求体**：

```json
{
  "context": {
    "file_type": "typescript",
    "directory": "src/components",
    "content": "示例代码内容...",
    "active_rules": ["rule-001"]
  }
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "rule_id": "rule-002",
        "name": "React组件规则",
        "relevance": 0.95,
        "reason": "与当前编辑的React组件文件高度相关"
      },
      {
        "rule_id": "rule-005",
        "name": "TypeScript组件类型规则",
        "relevance": 0.85,
        "reason": "提供TypeScript与React结合的最佳实践"
      }
    ]
  }
}
```

## 模板管理API

### 获取模板列表

获取可用的规则模板列表。

**请求**：

```
GET /templates
```

**查询参数**：

- `rule_type`: 规则类型(agent|auto|manual|always)
- `search`: 搜索关键词
- `page`: 页码(默认1)
- `limit`: 每页数量(默认10)

**响应**：

```json
{
  "success": true,
  "data": [
    {
      "id": "template-001",
      "name": "基础代理规则模板",
      "description": "适用于创建标准代理规则的模板",
      "rule_type": "agent",
      "created_at": "2025-03-01T00:00:00Z",
      "updated_at": "2025-03-10T00:00:00Z",
      "placeholders": [
        {
          "name": "RULE_NAME",
          "description": "规则名称",
          "required": true
        },
        {
          "name": "RULE_DESCRIPTION",
          "description": "规则描述",
          "required": true
        }
      ]
    },
    ...
  ],
  "meta": {
    "page": 1,
    "limit": 10,
    "total": 15
  }
}
```

### 获取单个模板

获取单个模板的详细信息。

**请求**：

```
GET /templates/{id}
```

**路径参数**：

- `id`: 模板ID

**响应**：

```json
{
  "success": true,
  "data": {
    "id": "template-001",
    "name": "基础代理规则模板",
    "description": "适用于创建标准代理规则的模板",
    "rule_type": "agent",
    "structure": "---\ndescription: {{RULE_DESCRIPTION}}\nglobs: {{RULE_GLOBS}}\nalwaysApply: false\n---\n\n# {{RULE_NAME}}\n\n## 关键规则\n\n{{RULE_CONTENT}}\n\n## 示例\n\n<example>\n{{EXAMPLE_CONTENT}}\n</example>\n\n<example type=\"invalid\">\n{{INVALID_EXAMPLE}}\n</example>",
    "created_at": "2025-03-01T00:00:00Z",
    "updated_at": "2025-03-10T00:00:00Z",
    "placeholders": [
      {
        "name": "RULE_NAME",
        "description": "规则名称",
        "required": true
      },
      {
        "name": "RULE_DESCRIPTION",
        "description": "规则描述",
        "required": true
      },
      {
        "name": "RULE_GLOBS",
        "description": "适用文件模式",
        "required": true,
        "default_value": "[]"
      },
      {
        "name": "RULE_CONTENT",
        "description": "规则内容",
        "required": true
      },
      {
        "name": "EXAMPLE_CONTENT",
        "description": "有效示例",
        "required": true
      },
      {
        "name": "INVALID_EXAMPLE",
        "description": "无效示例",
        "required": true
      }
    ],
    "default_metadata": {
      "author": "VibeCopilot Team",
      "tags": ["template-generated"]
    }
  }
}
```

### 应用模板

应用模板生成规则。

**请求**：

```
POST /templates/{id}/apply
```

**路径参数**：

- `id`: 模板ID

**请求体**：

```json
{
  "values": {
    "RULE_NAME": "React组件规则",
    "RULE_DESCRIPTION": "React组件开发的最佳实践规则",
    "RULE_GLOBS": ["*.tsx", "src/components/**/*.ts"],
    "RULE_CONTENT": "- 组件应遵循单一职责原则\n- 使用函数组件和Hooks\n- 使用PropTypes或TypeScript类型\n- 避免内联样式",
    "EXAMPLE_CONTENT": "function Button({ label, onClick }) {\n  return <button onClick={onClick}>{label}</button>\n}",
    "INVALID_EXAMPLE": "class Button extends React.Component {\n  render() {\n    return <button style={{color: 'red'}}>{this.props.label}</button>\n  }\n}"
  },
  "metadata": {
    "tags": ["react", "components"],
    "dependencies": ["rule-001"]
  }
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "rule": {
      "id": "rule-003",
      "name": "React组件规则",
      "type": "agent",
      "description": "React组件开发的最佳实践规则",
      "globs": ["*.tsx", "src/components/**/*.ts"],
      "alwaysApply": false,
      "content": "---\ndescription: React组件开发的最佳实践规则\nglobs: [\"*.tsx\", \"src/components/**/*.ts\"]\nalwaysApply: false\n---\n\n# React组件规则\n\n## 关键规则\n\n- 组件应遵循单一职责原则\n- 使用函数组件和Hooks\n- 使用PropTypes或TypeScript类型\n- 避免内联样式\n\n## 示例\n\n<example>\nfunction Button({ label, onClick }) {\n  return <button onClick={onClick}>{label}</button>\n}\n</example>\n\n<example type=\"invalid\">\nclass Button extends React.Component {\n  render() {\n    return <button style={{color: 'red'}}>{this.props.label}</button>\n  }\n}\n</example>",
      "version": "1.0.0",
      "created_at": "2025-04-03T00:00:00Z",
      "updated_at": "2025-04-03T00:00:00Z",
      "metadata": {
        "author": "VibeCopilot Team",
        "tags": ["react", "components", "template-generated"],
        "dependencies": ["rule-001"],
        "usage_count": 0,
        "effectiveness": 0
      }
    }
  }
}
```

## 分析API

### 分析规则依赖

分析规则的依赖关系。

**请求**：

```
POST /analysis/dependencies
```

**请求体**：

```json
{
  "rule_id": "rule-002"
}
```

或

```json
{
  "content": "规则内容..."
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "dependencies": [
      {
        "id": "rule-001",
        "name": "TypeScript最佳实践",
        "type": "explicit"
      },
      {
        "id": "rule-005",
        "name": "命名规范",
        "type": "implicit"
      }
    ],
    "dependents": [
      {
        "id": "rule-003",
        "name": "React Hook规则"
      },
      {
        "id": "rule-007",
        "name": "组件测试规则"
      }
    ],
    "graph": {
      "nodes": [...],
      "edges": [...]
    }
  }
}
```

### 检测规则冲突

检测多个规则之间的潜在冲突。

**请求**：

```
POST /analysis/conflicts
```

**请求体**：

```json
{
  "rule_ids": ["rule-001", "rule-002", "rule-003"]
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "has_conflicts": true,
    "conflicts": [
      {
        "rule1": {
          "id": "rule-001",
          "name": "TypeScript最佳实践"
        },
        "rule2": {
          "id": "rule-003",
          "name": "React Hook规则"
        },
        "type": "directive_conflict",
        "description": "规则1要求使用接口而规则3鼓励使用类型别名",
        "severity": "moderate",
        "resolution_suggestion": "明确指定接口和类型别名的使用场景"
      }
    ]
  }
}
```

### 评估规则有效性

评估规则的有效性和使用情况。

**请求**：

```
GET /analysis/effectiveness/{id}
```

**路径参数**：

- `id`: 规则ID

**响应**：

```json
{
  "success": true,
  "data": {
    "rule_id": "rule-002",
    "name": "React组件规则",
    "metrics": {
      "usage_count": 42,
      "effectiveness": 85,
      "application_rate": 0.78,
      "rejection_rate": 0.05,
      "modification_rate": 0.15
    },
    "feedback": {
      "positive": 15,
      "neutral": 5,
      "negative": 2
    },
    "history": [
      {
        "version": "1.0.0",
        "effectiveness": 75,
        "date": "2025-03-15T00:00:00Z"
      },
      {
        "version": "1.1.0",
        "effectiveness": 85,
        "date": "2025-04-03T00:00:00Z"
      }
    ],
    "recommendations": [
      "添加更多实际示例可能提高应用率",
      "规则的第三条指导原则经常被修改，考虑调整"
    ]
  }
}
```

## 错误码

| 错误码 | 描述 | HTTP状态码 |
|-------|------|-----------|
| `INVALID_REQUEST` | 无效的请求参数 | 400 |
| `RESOURCE_NOT_FOUND` | 请求的资源不存在 | 404 |
| `VALIDATION_ERROR` | 验证错误 | 422 |
| `CONFLICT_ERROR` | 资源冲突 | 409 |
| `INTERNAL_ERROR` | 内部服务器错误 | 500 |
| `UNAUTHORIZED` | 未授权访问 | 401 |
| `FORBIDDEN` | 禁止访问 | 403 |

## API限流

API实施了限流策略：

- 匿名请求：60次/小时
- 认证请求：1000次/小时

超过限制将返回429状态码（Too Many Requests）。

## 版本控制

API使用URI版本控制:

- 当前版本: `/api/v1`
- 未来版本: `/api/v2`

旧版本将在发布新版本12个月后弃用。
