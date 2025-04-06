# 路线图多图实现 (Roadmap Multimap Implementation)

本文档描述了VibeCopilot中路线图模块对多路线图的支持实现，包括架构变更、数据模型调整和命令行接口更新。

## 概述

VibeCopilot的路线图模块原本只支持单一路线图，现在已升级为支持多路线图管理，允许用户在不同路线图之间切换，以及独立管理每个路线图的内容。

## 架构变更

### 数据模型

1. 新增 `Roadmap` 实体类：
   - 定义了路线图的基本属性，包括ID、名称、描述和状态
   - 增加了 `is_active` 标志用于标识当前活动路线图

2. 现有实体关联：
   - 在 `Epic`、`Milestone`、`Story` 和 `Task` 实体中添加了 `roadmap_id` 字段
   - 所有实体通过 `roadmap_id` 与特定路线图关联

### 数据库服务

1. 数据库表结构调整：
   - 添加了 `roadmaps` 表，存储所有路线图信息
   - 在 `epics`、`milestones`、`stories` 和 `tasks` 表中添加了 `roadmap_id` 外键字段

2. 数据库服务增强：
   - 增加了路线图管理方法：创建、获取、更新、删除和列出路线图
   - 实现了活动路线图切换功能
   - 修改了所有CRUD操作以支持路线图ID过滤

### 数据同步

1. `DataSynchronizer` 类更新：
   - 支持按路线图ID导出YAML文件
   - 导入YAML文件时保留路线图关联
   - GitHub同步时支持多路线图文件

## 命令行接口

新增了三个主要命令用于路线图管理：

1. **路线图切换命令** (`roadmap switch`)：
   - 在不同路线图之间切换
   - 创建新的路线图
   - 查看当前活动路线图信息

2. **路线图列表命令** (`roadmap list`)：
   - 显示所有可用的路线图
   - 查看特定路线图的详细信息

3. **路线图同步命令更新** (`roadmap sync`)：
   - 支持指定路线图ID进行同步操作
   - 支持一次性拉取所有路线图

## 实现细节

### 数据库设计

```
roadmaps表：
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- description (TEXT)
- status (TEXT)
- is_active (INTEGER)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

所有相关表添加 `roadmap_id` 字段并设置外键约束。

### 路线图YAML文件命名

为支持多路线图，YAML文件命名采用 `roadmap_${roadmap_id}.yaml` 格式，例如：

- roadmap_RM1.yaml
- roadmap_RM2.yaml

## 使用示例

### 路线图切换

```bash
# 列出所有路线图
roadmap list

# 切换到特定路线图
roadmap switch RM1

# 创建新路线图
roadmap switch --create --name "产品开发路线图" --description "2024年产品开发计划"
```

### 路线图同步

```bash
# 将当前活动路线图同步到GitHub
roadmap sync --push

# 从GitHub拉取特定路线图
roadmap sync --pull --roadmap RM1

# 从GitHub拉取所有路线图
roadmap sync --pull --all

# 导出特定路线图到YAML
roadmap sync --export --roadmap RM2
```

## 后续改进

1. 路线图模板支持 - 允许从预定义模板创建新路线图
2. 路线图复制功能 - 基于现有路线图快速创建相似路线图
3. 路线图归档和恢复 - 支持不常用路线图的归档和必要时的恢复
4. 分组管理 - 将路线图按项目或团队分组
5. 权限控制 - 为不同路线图设置不同的访问权限

## 总结

多路线图支持大大增强了VibeCopilot的项目管理能力，使其能够同时管理多个项目或产品线的路线图。用户现在可以在不同路线图之间轻松切换，并保持各自的数据独立性，同时还能充分利用系统提供的YAML和GitHub同步功能。
