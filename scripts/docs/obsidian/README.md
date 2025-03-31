# 文档同步工具

这个目录包含用于在Obsidian和VibeCopilot项目文档之间同步内容的脚本。

## 快速开始

### Windows用户

1. **一次性同步**：双击 `run_sync_once.bat` 执行一次完整同步
2. **持续监控**：双击 `sync_to_obsidian.bat` 启动实时监控

### Mac/Linux用户

1. **一次性同步**：
   ```bash
   chmod +x run_sync_once.sh
   ./run_sync_once.sh
   ```

2. **持续监控**：
   ```bash
   chmod +x sync_to_obsidian.sh
   ./sync_to_obsidian.sh
   ```

## 高级用法

所有脚本都是基于 `obsidian_sync.py` 实现的，您可以直接使用该脚本获得更多高级功能：

```bash
# 查看帮助
python obsidian_sync.py

# 验证文档链接
python obsidian_sync.py --validate

# 创建新文档
python obsidian_sync.py --create-doc "用户/教程/示例.md" --title "示例教程" --category "教程"
```

## 常见问题

1. **脚本无法运行**：确保已安装Python和必要的依赖
2. **同步失败**：检查文档路径和权限
3. **链接不正确**：使用 `--validate` 参数检查链接

## 更多信息

详细的Obsidian集成指南请参阅 `/docs/user/tutorials/obsidian/obsidian_integration_guide.md`。
