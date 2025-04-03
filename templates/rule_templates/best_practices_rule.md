---
description: {{ description }}
globs: {{ globs }}
alwaysApply: {{ always_apply|default(false) }}
---

# {{ language_name }}最佳实践规则

## 规则目的

提供{{ language_name }}开发的最佳实践指南，确保代码质量、可维护性和性能。本规则适用于所有{{ language_name }}相关开发工作。

## 编码规范

{% for standard in coding_standards %}

### {{ standard.name }}

{{ standard.description }}

```{{ language_extension }}
{{ standard.example }}
```
{% endfor %}

## 架构模式

{% for pattern in architecture_patterns %}

### {{ pattern.name }}

{{ pattern.description }}

**何时使用**：{{ pattern.when_to_use }}

**示例结构**：
```
{{ pattern.structure }}
```
{% endfor %}

## 性能优化

{% for optimization in performance_optimizations %}

### {{ optimization.name }}

{{ optimization.description }}

**不良实践**：
```{{ language_extension }}
{{ optimization.bad_example }}
```

**推荐实践**：
```{{ language_extension }}
{{ optimization.good_example }}
```
{% endfor %}

## 安全最佳实践

{% for practice in security_practices %}

### {{ practice.name }}

{{ practice.description }}

**避免**：
```{{ language_extension }}
{{ practice.avoid_example }}
```

**推荐**：
```{{ language_extension }}
{{ practice.recommended_example }}
```
{% endfor %}

## 测试策略

{% for strategy in testing_strategies %}

### {{ strategy.name }}

{{ strategy.description }}

**示例**：
```{{ language_extension }}
{{ strategy.example }}
```
{% endfor %}

## 工具与库推荐

{% for tool in tools_libraries %}

### {{ tool.name }}

**用途**：{{ tool.purpose }}
**优势**：{{ tool.advantages }}
**使用示例**：
```{{ language_extension }}
{{ tool.example }}
```
{% endfor %}

## 参考资源

{% for resource in resources %}

- [{{ resource.name }}]({{ resource.url }})：{{ resource.description }}
{% endfor %}
