---
title: {{feature_name}} 开发指南
version: {{version}}
created_at: {{created_at}}
updated_at: {{updated_at}}
epic_id: {{epic_id}}
status: draft
---

# {{feature_name}} 开发指南

## 架构概述

{{architecture_overview}}

```mermaid
{{architecture_diagram}}
```

## 核心组件

### {{component_1}}

**职责:** {{component_1_responsibility}}

**关键文件:**

- `{{file_path_1}}`: {{file_description_1}}
- `{{file_path_2}}`: {{file_description_2}}

**重要接口:**
```typescript
{{component_1_interface}}
```

### {{component_2}}

**职责:** {{component_2_responsibility}}

**关键文件:**

- `{{file_path_3}}`: {{file_description_3}}
- `{{file_path_4}}`: {{file_description_4}}

## 数据流

1. {{data_flow_step_1}}
2. {{data_flow_step_2}}
3. {{data_flow_step_3}}

## 开发环境设置

```bash
{{setup_commands}}
```

## API参考

### {{api_endpoint_1}}

**请求:**
```json
{{request_example_1}}
```

**响应:**
```json
{{response_example_1}}
```

### {{api_endpoint_2}}

**请求:**
```json
{{request_example_2}}
```

**响应:**
```json
{{response_example_2}}
```

## 测试指南

### 单元测试

```bash
{{unit_test_command}}
```

关键测试用例:

- {{test_case_1}}
- {{test_case_2}}

### 集成测试

```bash
{{integration_test_command}}
```

## 部署流程

1. {{deployment_step_1}}
2. {{deployment_step_2}}
3. {{deployment_step_3}}

## 故障排除与调试

### 常见错误

| 错误信息 | 可能原因 | 解决方案 |
| -------- | -------- | -------- |
| {{error_1}} | {{cause_1}} | {{solution_1}} |
| {{error_2}} | {{cause_2}} | {{solution_2}} |

### 日志查看

```bash
{{log_commands}}
```

## 后续开发建议

- {{future_improvement_1}}
- {{future_improvement_2}}
- {{future_improvement_3}}

## 技术债务

| 问题 | 优先级 | 描述 |
| ---- | ------ | ---- |
| {{tech_debt_1}} | {{priority_1}} | {{description_1}} |
| {{tech_debt_2}} | {{priority_2}} | {{description_2}} |

## 变更记录

| 版本 | 日期 | 变更内容 |
| ---- | ---- | -------- |
| {{version}} | {{created_at}} | 初始版本 |

---
注意: 将状态从"draft"更改为"approved"以发布此开发指南
