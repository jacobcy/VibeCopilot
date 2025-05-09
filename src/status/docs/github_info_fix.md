# GitHub信息警告修复文档

## 问题描述

系统出现"状态服务未返回有效的GitHub信息"的警告，导致路线图无法正确显示GitHub相关信息。

## 根本原因

1. 多个配置文件中的GitHub项目ID不一致
2. roadmap_data.py中的警告日志会在获取GitHub信息失败时触发，即使后续有备用方案
3. 服务连接未正确初始化，导致状态服务与路线图服务之间信息传递不畅

## 解决方案

### 1. 配置文件统一

创建以下配置文件并确保它们中的GitHub信息一致：

- `.vibecopilot/config/settings.json` - 主配置文件
- `.vibecopilot/github_info.json` - GitHub信息配置
- `.repomix/instructions/roadmap-instructions.md` - Roadmap指令文件

将GitHub项目ID设为1（数字类型，而非字符串），确保所有配置保持一致。

### 2. 修改代码逻辑

修改`src/roadmap/service/roadmap_data.py`中的获取GitHub信息逻辑：

- 创建新的`_get_github_info`函数，优先从状态服务获取信息，失败时从配置获取，最后使用默认值
- 改进`get_roadmap_info`函数中获取GitHub信息的部分，使用新函数并确保始终能提供值
- 移除不必要的警告日志，改为更适合的INFO级别日志

### 3. 修复服务连接

在`src/roadmap/service/service_connector.py`中添加`force_connect_services`函数：

- 强制重新初始化服务连接
- 更新GitHub信息提供者的配置
- 确保路线图服务能够获取GitHub信息

### 4. 创建修复脚本

创建两个脚本用于自动化修复：

1. `scripts/fix_github_project_id.py` - 同步所有配置文件中的GitHub项目ID
2. `src/fix_roadmap_connection.py` - 修复路线图服务与状态服务的连接

## 测试与验证

运行`vc status show`命令确认：

1. 不再出现"状态服务未返回有效的GitHub信息"警告
2. GitHub仓库信息正确显示
3. 路线图中包含正确的GitHub链接信息

## 注意事项

1. 项目ID在实际应用中应该由GitHub API自动检测或创建，本修复使用了默认值1
2. 由于GitHub API不断演进，自动检测代码需要定期更新
3. 建议未来实现完整的配置同步机制，确保所有配置文件保持一致

## 未来改进

1. 实现自动检测GitHub项目ID并更新配置的功能
2. 增加配置验证逻辑，确保值的一致性
3. 改进错误处理，避免不必要的警告日志
