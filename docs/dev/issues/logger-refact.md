# VibeCopilot 日志系统与控制台打印统一方案

## 1. 背景与问题

当前 VibeCopilot 项目中存在多种日志记录和控制台输出方式：

1. **标准 `logging` 模块:** 部分模块使用。
2. **自定义 `Logger` 类 (`src/core/logger.py`):** 提供了简单的日志封装，但功能有限，且与标准 `logging` 存在割裂。
3. **`print()` 语句:** 大量用于调试、状态输出和用户交互。
4. **`click.echo()`:** 用于 CLI 输出。
5. **`rich.print()` / `Console`:** 用于格式化输出。
6. **特定模块的控制台工具 (`src/roadmap/sync/utils/console.py`):** 功能重复。

这种混乱导致：

* **配置困难:** 无法统一配置日志级别、格式和输出目标。
* **输出不一致:** 控制台输出风格各异，用户体验不佳。
* **维护成本高:** 需要维护多套日志和打印逻辑。
* **调试追踪难:** 日志分散，难以追踪完整的执行流程。
* **功能缺失:** 缺乏结构化日志、日志轮转、不同目标（文件、数据库、控制台）的灵活路由等高级功能。

**目标:** 建立一套统一、灵活、可配置的日志系统和控制台输出规范，提升开发效率、可维护性和用户体验。

## 2. 统一方案

采用 Python 标准 `logging` 模块作为核心，结合 `rich` 库进行控制台美化，并通过 YAML 文件进行配置。

### 2.1 核心组件

* **`logging`:** Python 内置日志库，提供基础框架。
* **`rich`:** 用于创建美观、信息丰富的控制台输出，特别是 `rich.logging.RichHandler`。
* **`PyYAML`:** 用于加载 `logging.yaml` 配置文件。
* **`logging.yaml`:** 集中管理日志配置（格式、处理器、级别等）。
* **`src/core/log_init.py`:** 负责读取配置并初始化 `logging` 系统。
* **`src/core/log_config.py`:** (可选) 提供默认的 Python 字典格式配置，作为 `logging.yaml` 不存在时的备选。
* **`src/logger/handlers.py`:** 包含自定义 Handler，例如将日志写入数据库的 `DatabaseLogHandler`。
* **`src/utils/console_utils.py`:** 提供一组基于 `rich.console.Console` 的标准化函数，用于向用户显示信息、成功、警告、错误等。

### 2.2 架构设计

```
VibeCopilot/
├── config/
│   └── logging.yaml              # 日志配置文件
├── src/
│   ├── core/
│   │   ├── log_config.py         # (可选) 默认配置字典
│   │   └── log_init.py           # 日志初始化模块
│   ├── logger/
│   │   ├── __init__.py
│   │   └── handlers.py           # 自定义 Handler
│   └── utils/
│       └── console_utils.py      # 控制台工具函数
└── 其他模块...
```

### 2.3 日志初始化 (`src/core/log_init.py`)

* 提供 `init_logging()` 函数。
* 负责创建必要的日志目录。
* 优先加载 `config/logging.yaml` 文件。
* 如果 YAML 文件不存在，则加载 `src/core/log_config.py` 中的 `DEFAULT_LOGGING_CONFIG`。
* 使用 `logging.config.dictConfig()` 应用配置。

### 2.4 日志配置 (`config/logging.yaml` 或 `src/core/log_config.py`)

* 定义 formatters (日志格式)。
* 定义 handlers (处理器，如控制台 `RichHandler`、文件 `RotatingFileHandler`、自定义 `DatabaseLogHandler` 等)。
* 定义 loggers (指定不同模块使用的 handlers 和最低日志级别)。
* 支持根 logger 和特定模块 logger 的配置。

### 2.5 自定义处理器 (`src/logger/handlers.py`)

* `DatabaseLogHandler`: 将特定级别的日志（如 INFO 及以上的工作流日志，ERROR 日志）写入数据库（如 `OperationLog`, `ErrorLog` 表）。
* (可选) `WorkflowFileHandler`: 可根据日志记录中的上下文信息（如 `workflow_id`, `session_id`）动态决定日志文件路径。

### 2.6 控制台工具 (`src/utils/console_utils.py`)

* 基于 `rich.console.Console`。
* 提供标准化函数：`print_info`, `print_success`, `print_warning`, `print_error`, `print_table`, `ask_confirm`。
* 确保用户看到的控制台输出风格统一、信息清晰。

## 3. 迁移指南

### 3.1 日志系统迁移

**统一方式:** 在需要记录日志的模块中，直接使用标准 `logging` 获取 logger 实例。

```python
import logging

logger = logging.getLogger(__name__)

# 普通日志
logger.info("这是一个普通信息日志")
logger.debug("这是一个调试日志")

# 记录带上下文的工作流日志 (如果配置了相应处理器和格式器)
logger.info("工作流操作完成", extra={
    "workflow_id": workflow_id,
    "session_id": session_id,
    "stage_id": stage_id
})
```

### 3.2 控制台打印迁移

**统一方式:** 使用 `src/utils/console_utils.py` 提供的函数。

```python
from src.utils.console_utils import print_error, print_warning, print_success, print_info

# 错误信息
print_error(f"操作失败: {error_message}")

# 警告信息
print_warning("找不到指定的配置文件，将使用默认配置")

# 成功信息
print_success("操作成功完成")

# 普通信息
print_info("正在处理请求...")
```

### 3.3 何时使用日志 vs 控制台打印

#### 使用日志 (`logger.*`)

* 记录程序内部运行状态、流程、调试信息。
* 记录错误和异常的技术细节，用于问题排查。
* 记录需要长期存储或用于分析的操作记录（如数据库日志）。
* 不应直接展示给最终用户的技术性信息。

#### 使用控制台打印 (`console_utils.*`)

* 向最终用户显示操作结果、状态更新。
* 提供用户交互提示（如确认、输入）。
* 显示格式化的数据（如表格）。
* 用户需要直接看到的信息。

## 4. 下一步工作

1. **替换 `print` 调用:**
    * 全局搜索项目中的 `print()` 语句。
    * 根据 3.3 节的原则，将用于调试和内部状态输出的 `print` 替换为 `logger.debug()` 或 `logger.info()`。
    * 将用于用户界面显示的 `print` 替换为 `src/utils/console_utils.py` 中的相应函数。
    * 移除不再需要的 `print()` 语句和旧的控制台工具（如 `src/roadmap/sync/utils/console.py`）。
2. **完善与测试:**
    * 编写或完善日志系统的单元测试和集成测试。
    * 验证不同场景下的日志级别、格式和输出（控制台、文件、数据库）。
    * 确保 `rich` 的控制台输出在各种终端下表现正常。
    * 进行必要的性能测试和调优。
    * 更新相关开发文档和代码注释。

## 5. 注意事项

* **配置热加载:** 当前方案不支持日志配置的热加载。如果需要修改配置，需要重启应用。
* **性能:** 大量日志记录，特别是写入数据库或频繁的文件 IO，可能会影响性能。需要根据实际情况调整日志级别和 Handler 配置。
* **上下文传递:** 对于需要在日志中记录特定上下文（如 `workflow_id`）的情况，需要确保这些信息通过 `extra` 参数传递给日志记录函数。
* **依赖管理:** 确保 `PyYAML` 和 `rich` 已添加到项目依赖中。
* **安全:** 避免在日志中记录敏感信息（如密码、API 密钥）。
