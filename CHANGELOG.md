# Changelog

## [Unreleased]

### Added

- 规则模板引擎系统 (TS10.1.1)
  - 基于Jinja2的模板引擎
  - 模板管理器和规则生成器
  - 核心规则模板实现
  - 模板变量验证和替换机制

### Fixed

- 修复了 roadmap_service.py 中的导入错误 (`src.db.database` → `src.db.connection_manager`)
- 修复 `vc status` 命令因导入错误而无法运行的问题

## [0.1.0] - 2023-04-01

### Added

- 初始项目结构
- 基础命令系统
- GitHub接口封装
- 文档系统
