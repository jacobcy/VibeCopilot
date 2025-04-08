---
description: API文档模板，用于创建API接口文档
variables:
  - name: title
    description: API标题
    required: true
    type: string
  - name: description
    description: API描述
    required: true
    type: string
  - name: name
    description: API接口名称
    required: true
    type: string
  - name: date
    description: 创建/更新日期
    required: false
    type: string
    default: "{{current_date}}"
type: doc
author: VibeCopilot
version: 1.0.0
tags:
  - api
  - documentation
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
