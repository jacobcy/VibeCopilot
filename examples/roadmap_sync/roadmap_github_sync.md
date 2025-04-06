# 路线图GitHub同步指南

> **最后更新日期：** 2024年6月6日

## 概述

本文档提供路线图与GitHub项目同步的详细指南，涵盖功能介绍、准备工作、使用方法、实现细节以及故障排除。

VibeCopilot路线图GitHub同步功能实现了：

- 路线图数据从YAML文件到系统数据库的导入
- 路线图数据从系统到GitHub项目的双向同步
- 使用路线图theme字段关联GitHub项目ID

## 准备工作

### 环境变量配置

使用GitHub同步功能需设置以下环境变量：

```bash
# GitHub认证与仓库配置
export GITHUB_TOKEN=your_github_personal_access_token  # 必须包含repo和project权限
export GITHUB_OWNER=your_github_username_or_organization
export GITHUB_REPO=your_github_repository_name

# 可选调试配置
export MOCK_SYNC=true  # 开发测试时使用，避免真实API调用
export DEBUG_SYNC=true  # 显示详细日志
```

### 路线图YAML格式

路线图YAML文件应包含以下核心字段：

```yaml
title: "规则引擎路线图"  # 路线图标题
description: "VibeCopilot规则引擎开发路线图"  # 路线图描述
theme: ""  # GitHub项目ID，可通过同步更新

milestones:  # 里程碑列表
  - title: "基础设施"
    description: "建立规则引擎基础框架"
  - title: "核心功能"
    description: "实现规则解析和执行功能"

tasks:  # 任务列表
  - title: "定义规则格式"
    description: "设计规则的标准格式结构"
    milestone: "基础设施"
    priority: "P1"
```

## 使用流程

完整的GitHub同步流程包含三个关键步骤：

### 1. 导入路线图数据

将YAML文件导入系统数据库：

```python
from src.roadmap.service import RoadmapService

roadmap_service = RoadmapService()
result = roadmap_service.import_from_yaml(
    ".ai/roadmap/rule_engine_roadmap.yaml",
    "roadmap-rule-engine-roadmap"
)

print(f"导入结果: {result.get('success')}")
```

### 2. 更新Theme字段（关联GitHub项目）

更新路线图theme字段为GitHub项目ID：

```python
import yaml
import tempfile
import os

# 读取YAML并修改theme
yaml_path = ".ai/roadmap/rule_engine_roadmap.yaml"
with open(yaml_path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

# 设置theme为GitHub项目ID
data["theme"] = "123456"  # 替换为实际GitHub项目ID

# 创建临时文件
temp_fd, temp_path = tempfile.mkstemp(suffix=".yaml")
os.close(temp_fd)

# 写入修改后的数据
with open(temp_path, "w", encoding="utf-8") as f:
    yaml.dump(data, f, default_flow_style=False)

# 重新导入
roadmap_service = RoadmapService()
result = roadmap_service.import_from_yaml(temp_path, "roadmap-rule-engine-roadmap")

# 清理
os.remove(temp_path)
```

### 3. 执行同步

将路线图数据同步到GitHub并从GitHub同步状态更新：

```python
import os
from src.roadmap.service import RoadmapService

# 初始化
roadmap_service = RoadmapService()
roadmap_id = "roadmap-rule-engine-roadmap"
roadmap_service.set_active_roadmap(roadmap_id)

# 执行同步（开发时使用模拟模式）
os.environ["MOCK_SYNC"] = "true"  # 开发/测试时使用
sync_result = roadmap_service.sync_to_github(roadmap_id)

# 验证结果
if sync_result.get("success"):
    print(f"同步成功! GitHub项目: {sync_result.get('github_project')}")

    # 从GitHub同步状态回路线图
    status_result = roadmap_service.sync_from_github(roadmap_id)
    if status_result.get("success"):
        print("状态同步成功!")
else:
    print(f"同步失败: {sync_result.get('error')}")
```

## 实现架构

路线图GitHub同步功能的技术实现包括：

### 关键组件

- **RoadmapService**: 核心服务，整合各种同步功能
- **YamlSyncService**: 处理YAML文件导入/导出
- **GitHubSyncService**: 处理与GitHub的双向同步

### 数据流向

```
YAML文件 → YamlSyncService → 数据库 → GitHubSyncService → GitHub Projects
                                  ↑                            |
                                  └────────────────────────────┘
                                       状态同步回路线图
```

### 同步过程

同步过程分三个阶段：

1. **导入阶段**：将YAML数据导入系统数据库
2. **更新阶段**：更新theme字段为GitHub项目ID
3. **同步阶段**：
   - 正向同步：数据库 → GitHub (路线图、里程碑、任务)
   - 反向同步：GitHub → 数据库 (状态更新)

## 高级用法

### 自定义模拟数据处理

针对数据库问题，可使用自定义函数替代默认数据访问方法：

```python
def patch_get_roadmap(service, roadmap_id):
    """替代get_roadmap的模拟数据函数"""
    yaml_path = ".ai/roadmap/rule_engine_roadmap.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {
        "id": roadmap_id,
        "name": data.get("title", "规则引擎路线图"),
        "description": data.get("description"),
        "theme": data.get("theme", "")
    }

# 应用补丁
roadmap_service.get_roadmap = lambda rid: patch_get_roadmap(roadmap_service, rid)
```

### 增量同步

仅同步更改过的数据：

```python
# 增量同步示例（待实现）
roadmap_service.sync_to_github(roadmap_id, incremental=True)
```

## 常见问题与解决方案

### 1. 数据库查询错误

**症状:**
```
Column expression, FROM clause, or other columns clause element expected, got <class 'src.models.db.roadmap.Epic'>.
```

**解决方案:**

- 使用`final_github_sync.py`中的修补函数绕过数据库查询
- 确保使用模拟模式 `os.environ["MOCK_SYNC"] = "true"`

### 2. GitHub认证问题

**症状:**
```
401 Client Error: Unauthorized for url: https://api.github.com/repos/...
```

**解决方案:**

- 检查`GITHUB_TOKEN`是否设置正确
- 确保Token有足够权限（repo、project）
- 验证GitHub仓库名和组织/用户名拼写正确

### 3. 路线图数据不完整

**症状:**
同步失败，日志显示缺少数据

**解决方案:**

- 检查YAML格式是否符合要求
- 确保所有必需字段已填写
- 重新导入YAML文件

## 开发计划

未来的功能改进：

1. **数据库查询优化**: 修复实体类与SQL查询兼容性问题
2. **增量同步支持**: 仅同步发生变化的数据，提高效率
3. **冲突解决机制**: 处理双向同步中的数据冲突
4. **自动化测试用例**: 提供更完善的同步功能验证

## 参考资料

- [GitHub Projects API文档](https://docs.github.com/en/rest/reference/projects)
- [GitHub Issues API文档](https://docs.github.com/en/rest/reference/issues)
- [VibeCopilot路线图模块设计文档](./README.md)

---

如有问题，请联系开发团队: <vibeteam@example.com>
