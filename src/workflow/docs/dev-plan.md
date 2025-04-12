# VibeCopilot 工作流系统开发计划

## 系统架构

工作流系统采用模块化设计，主要由以下部分组成：

1. **核心操作层**：提供工作流的基本CRUD操作
2. **验证层**：确保工作流定义的有效性
3. **解析层**：负责从描述性内容生成工作流
4. **执行层**：运行和管理工作流执行
5. **CLI层**：提供命令行界面

## 技术栈

### 主要依赖

- **Python 3.9+**：基础开发语言
- **OpenAI API**：用于LLM解析功能
- **Rich**：用于命令行界面美化和交互
- **Click/Argparse**：命令行参数解析
- **SQLite**：轻量级数据库存储
- **JSON Schema**：用于工作流验证

### 文件存储

目前工作流系统使用文件系统存储：

- 工作流定义：`data/workflows/` 目录下的JSON文件
- 工作流模板：`templates/flow/` 目录下的JSON文件
- 工作流执行记录：`data/workflow_executions/` 目录下的JSON文件

### 未来数据库设计

计划迁移到SQLite数据库，主要表结构：

1. **Workflows表**：存储工作流元数据
   ```sql
   CREATE TABLE workflows (
     id TEXT PRIMARY KEY,
     name TEXT NOT NULL,
     description TEXT,
     version TEXT,
     created_at TIMESTAMP,
     updated_at TIMESTAMP,
     definition JSON  -- 完整的工作流定义JSON
   );
   ```

2. **Stages表**：存储工作流阶段
   ```sql
   CREATE TABLE stages (
     id TEXT PRIMARY KEY,
     workflow_id TEXT,
     name TEXT NOT NULL,
     description TEXT,
     order_index INTEGER,
     checklist JSON,
     deliverables JSON,
     FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
   );
   ```

3. **Transitions表**：存储阶段间转换
   ```sql
   CREATE TABLE transitions (
     id TEXT PRIMARY KEY,
     workflow_id TEXT,
     from_stage TEXT,
     to_stage TEXT,
     condition TEXT,
     FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
     FOREIGN KEY (from_stage) REFERENCES stages(id) ON DELETE CASCADE,
     FOREIGN KEY (to_stage) REFERENCES stages(id) ON DELETE CASCADE
   );
   ```

4. **Sessions表**：存储工作流执行会话
   ```sql
   CREATE TABLE sessions (
     id TEXT PRIMARY KEY,
     workflow_id TEXT,
     name TEXT,
     status TEXT,
     created_at TIMESTAMP,
     updated_at TIMESTAMP,
     FOREIGN KEY (workflow_id) REFERENCES workflows(id)
   );
   ```

5. **StageInstances表**：存储阶段执行实例
   ```sql
   CREATE TABLE stage_instances (
     id TEXT PRIMARY KEY,
     session_id TEXT,
     stage_id TEXT,
     status TEXT,
     started_at TIMESTAMP,
     completed_at TIMESTAMP,
     checklist_status JSON,
     FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
     FOREIGN KEY (stage_id) REFERENCES stages(id)
   );
   ```

## 开发注意事项

### ID管理

1. **短ID格式**：
   - 使用8字符的UUID前缀作为ID
   - 确保ID在进行序列化和反序列化时保持不变

2. **ID兼容性**：
   - 支持长UUID向短ID的迁移
   - 在查找工作流时优先使用精确匹配，然后是模糊匹配

### 文件与数据库同步

为了平滑迁移至数据库系统：

1. **双写阶段**：
   - 实现数据库写入的同时保留文件写入
   - 添加兼容性检查，确保文件和数据库数据一致

2. **迁移工具**：
   - 提供从文件到数据库的迁移工具
   - 支持数据验证和校验功能

### 代码结构规范

1. **模块化**：
   - 每个功能组件应作为独立模块
   - 避免循环依赖，使用明确的依赖方向

2. **函数签名**：
   - 保持函数参数和返回值类型一致
   - 使用类型提示和文档字符串
   - 返回格式统一，使用dict带status和code

3. **错误处理**：
   - 使用自定义异常体系
   - 在适当的抽象层次处理异常
   - 提供详细的错误消息和错误代码

4. **日志记录**：
   - 使用分层的日志系统
   - 关键操作必须记录日志
   - 包含足够的上下文信息

### CLI交互规范

1. **命令格式**：
   - 使用一致的命令和子命令结构
   - 选项名称应直观且符合惯例

2. **输出格式**：
   - 支持多种输出格式（文本、JSON、图表）
   - 使用Rich库提供彩色和格式化输出
   - 错误信息清晰详细

3. **交互确认**：
   - 危险操作需要确认（如删除）
   - 支持--force选项跳过确认

## 工作流系统的核心逻辑

### 工作流创建

1. **基于描述的创建流程**：
   ```
   描述性文件 → OpenAI解析 → 工作流结构 → 验证 → 保存
   ```

2. **模板使用逻辑**：
   - 模板定义工作流的基本结构
   - OpenAI解析时考虑模板要求
   - 解析结果必须符合模板约束

### 工作流验证

1. **多层验证**：
   - 基础字段验证：检查必要字段存在性
   - 结构验证：确保阶段和转换结构正确
   - 引用验证：检查转换引用的阶段是否存在
   - 完整性验证：检查工作流是否完整连通
   - 循环检测：确保没有循环依赖

2. **验证器设计**：
   - 基础验证器抽象类
   - 专用验证器实现
   - 验证结果包含错误信息和位置

### 工作流执行

1. **会话模型**：
   - 一个工作流可以有多个执行会话
   - 会话包含多个阶段实例
   - 阶段实例记录执行状态和检查项状态

2. **状态转换**：
   - 阶段状态：未开始 → 进行中 → 已完成/已跳过
   - 会话状态：未开始 → 进行中 → 已完成/已取消

### 上下文管理

1. **上下文内容**：
   - 工作流元数据
   - 当前阶段信息
   - 已完成阶段的历史
   - 检查项状态
   - 相关的外部数据

2. **上下文提供者**：
   - 动态生成上下文
   - 支持模板化上下文格式
   - 可扩展以包含更多数据源

## 性能考虑

1. **内存使用**：
   - 避免在内存中加载所有工作流
   - 使用懒加载和分页技术

2. **AI服务调用**：
   - 实现缓存机制减少API调用
   - 添加重试逻辑处理间歇性失败
   - 在本地批处理请求

3. **文件I/O优化**：
   - 批量读写以减少文件系统操作
   - 考虑使用内存缓存

## 测试策略

1. **单元测试**：
   - 核心功能的独立测试
   - 使用模拟对象隔离依赖

2. **集成测试**：
   - 测试组件间交互
   - 验证完整流程

3. **特殊测试用例**：
   - 边界条件测试
   - 错误处理测试
   - 并发操作测试

## 下一步计划

### 近期任务

1. **数据库集成**：将文件存储迁移到SQLite数据库
2. **工作流模板管理**：完善模板CRUD操作
3. **API层实现**：提供REST API接口
4. **工作流版本控制**：支持工作流版本管理和比较

### 中期目标

1. **权限系统**：实现基于角色的访问控制
2. **工作流编辑器**：提供Web界面进行可视化编辑
3. **工作流统计**：提供执行统计和分析功能
4. **工作流导出/导入**：支持与其他系统交换工作流定义

### 长期愿景

1. **工作流引擎优化**：提高执行效率和扩展性
2. **自动化触发器**：基于事件或时间的自动触发
3. **动态工作流**：支持运行时修改工作流路径
4. **机器学习增强**：使用ML优化推荐和预测功能
