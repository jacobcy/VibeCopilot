# 规则引擎API规范

> **文档元数据**
> 版本: 1.0
> 更新日期: 2025-04-05
> 状态: 已审核
> 负责团队: 系统架构团队

## 1. API概述

规则引擎API是一组RESTful接口，提供规则和模板的创建、读取、更新、删除及其他管理功能。API使用JSON作为数据交换格式，遵循标准HTTP方法和状态码。

## 2. 基础信息

### 2.1 基础URL

```
/api/v1
```

### 2.2 认证方式

所有API请求需要通过Bearer Token认证：

```
Authorization: Bearer <token>
```

### 2.3 通用响应格式

**成功响应**:
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

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误信息",
    "details": { ... }
  }
}
```

## 3. 规则管理API

### 3.1 获取规则列表

获取规则列表，支持分页、过滤和排序。

**请求**:
```
GET /rules
```

**查询参数**:

- `type`: 规则类型(agent|auto|manual|always)
- `tags`: 标签(逗号分隔)
- `search`: 搜索关键词
- `page`: 页码(默认1)
- `limit`: 每页数量(默认10)
- `sort`: 排序字段
- `order`: 排序方向(asc|desc)

**响应示例**:
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
        "usage_count": 42
      }
    }
  ],
  "meta": {
    "page": 1,
    "limit": 10,
    "total": 42
  }
}
```

### 3.2 获取单个规则

根据ID获取单个规则的详细信息。

**请求**:
```
GET /rules/{id}
```

**响应字段说明**:

- `id`: 规则唯一标识符
- `name`: 规则名称
- `type`: 规则类型
- `description`: 规则描述
- `globs`: 适用的文件类型
- `alwaysApply`: 是否全局应用
- `content`: 规则内容(Markdown格式)
- `version`: 规则版本
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `metadata`: 元数据(作者、标签等)

### 3.3 创建规则

创建新规则。

**请求**:
```
POST /rules
```

**请求体字段**:

- `name`: 规则名称(必填)
- `type`: 规则类型(必填)
- `description`: 规则描述(必填)
- `globs`: 适用的文件类型(数组)
- `alwaysApply`: 是否全局应用(布尔值)
- `content`: 规则内容(Markdown格式)
- `metadata`: 元数据(对象)

### 3.4 更新规则

更新现有规则。

**请求**:
```
PUT /rules/{id}
```

### 3.5 删除规则

删除规则。

**请求**:
```
DELETE /rules/{id}
```

## 4. 模板管理API

### 4.1 获取模板列表

获取可用的规则模板列表。

**请求**:
```
GET /templates
```

### 4.2 获取单个模板

获取单个模板的详细信息。

**请求**:
```
GET /templates/{id}
```

### 4.3 创建模板

创建新的规则模板。

**请求**:
```
POST /templates
```

### 4.4 更新模板

更新现有模板。

**请求**:
```
PUT /templates/{id}
```

### 4.5 删除模板

删除模板。

**请求**:
```
DELETE /templates/{id}
```

### 4.6 应用模板

应用模板生成规则。

**请求**:
```
POST /templates/{id}/apply
```

## 5. 分析API

### 5.1 分析规则依赖

分析规则的依赖关系。

**请求**:
```
POST /analysis/dependencies
```

### 5.2 检测规则冲突

检测多个规则之间的潜在冲突。

**请求**:
```
POST /analysis/conflicts
```

### 5.3 评估规则有效性

评估规则的有效性和使用情况。

**请求**:
```
GET /analysis/effectiveness/{id}
```

## 6. 错误码

| 错误码 | 描述 | HTTP状态码 |
|-------|------|-----------|
| `INVALID_REQUEST` | 无效的请求参数 | 400 |
| `RESOURCE_NOT_FOUND` | 请求的资源不存在 | 404 |
| `VALIDATION_ERROR` | 验证错误 | 422 |
| `CONFLICT_ERROR` | 资源冲突 | 409 |
| `INTERNAL_ERROR` | 内部服务器错误 | 500 |
| `UNAUTHORIZED` | 未授权访问 | 401 |
| `FORBIDDEN` | 禁止访问 | 403 |

## 7. API限流

API实施了限流策略：

- 匿名请求：60次/小时
- 认证请求：1000次/小时

超过限制将返回429状态码（Too Many Requests）。

## 8. 版本控制

API使用URI版本控制:

- 当前版本: `/api/v1`
- 未来版本: `/api/v2`

旧版本将在发布新版本12个月后弃用。
