# 日志模块测试

本目录包含VibeCopilot日志模块的测试用例。

## 测试文件

- `test_workflow_log.py` - 工作流日志功能测试，验证日志服务的基本功能以及与现有工作流模块的兼容性

## 运行测试

从项目根目录运行测试：

```bash
# 运行单个测试文件
python -m src.logger.tests.test_workflow_log

# 使用pytest运行测试（如果已安装）
pytest src/log/tests/
```

## 测试数据

测试会在以下目录创建临时日志文件：

- `data/logs/workflow_executions/`
- `data/logs/workflow_operations/`

每次测试运行前会清理这些目录中的测试数据。
