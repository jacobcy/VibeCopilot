# 路线图模块测试

本目录包含VibeCopilot项目的路线图模块测试用例。测试涵盖了核心功能、同步功能和服务层接口的单元测试和集成测试。

## 测试结构

- `test_plan.md` - 测试计划文档
- `test_manager.py` - RoadmapManager单元测试
- `test_status.py` - RoadmapStatus单元测试
- `test_service.py` - RoadmapService单元测试
- `test_integration.py` - 路线图模块集成测试
- `run_tests.py` - 测试运行脚本

## 运行测试

可以通过以下方式运行测试：

1. 运行所有测试：

```bash
python tests/roadmap/run_tests.py
```

2. 运行单个测试文件：

```bash
python -m unittest tests/roadmap/test_manager.py
```

3. 运行特定测试类：

```bash
python -m unittest tests.roadmap.test_manager.TestRoadmapManager
```

4. 运行特定测试方法：

```bash
python -m unittest tests.roadmap.test_manager.TestRoadmapManager.test_check_roadmap_entire
```

## 测试覆盖范围

测试覆盖了路线图模块的以下关键功能：

1. **核心功能**
   - 路线图状态检查和更新
   - 里程碑进度计算
   - 任务状态管理

2. **同步功能**
   - 导出路线图到YAML文件
   - 从YAML文件导入路线图数据
   - GitHub项目同步

3. **路线图管理**
   - 创建和删除路线图
   - 切换活跃路线图
   - 获取路线图信息

## 依赖关系

测试使用了以下模块：

- `unittest` - Python标准测试框架
- `unittest.mock` - 用于创建模拟对象
- `tempfile` - 用于创建临时文件和目录

## 测试数据

测试使用模拟数据，不需要实际的数据库或外部服务。所有外部依赖都通过模拟对象来替代，确保测试的隔离性和可重复性。
