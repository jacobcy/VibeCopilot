# VibeCopilot Memory命令使用演示

> **重要说明**: 所有示例都基于`MemoryService`统一接口实现。VibeCopilot的memory模块采用门面(Facade)模式，统一封装了所有与知识库相关的功能，确保API一致性和实现解耦。CLI命令不直接依赖底层实现，只通过`MemoryService`接口访问功能。

本文档演示如何使用VibeCopilot的memory命令进行知识库管理，包括创建、查看、更新、删除和搜索笔记等操作。

## 准备工作

确认环境已正确配置：

```bash
# 确认vibecopilot命令可用
vibecopilot --version

# 确认Basic Memory已配置
basic-memory project list
```

## 基本操作演示

### 1. 创建笔记

创建笔记是最基本的操作，需要提供标题、存储目录和内容：

```bash
# 创建笔记的基本格式
vibecopilot memory create --title "笔记标题" --folder "存储目录" --content "笔记内容"

# 示例：创建开发笔记
vibecopilot memory create \
  --title "开发环境配置" \
  --folder "dev_notes" \
  --tags "开发,环境配置,python" \
  --content "# Python开发环境配置\n\n1. 安装Python 3.9+\n2. 创建虚拟环境\n3. 安装依赖包"
```

### 2. 查看笔记

可以通过路径查看笔记内容：

```bash
# 查看笔记的基本格式
vibecopilot memory show --path "目录/标题"

# 示例：查看刚才创建的笔记
vibecopilot memory show --path "dev_notes/开发环境配置"
```

### 3. 更新笔记

更新现有笔记的内容：

```bash
# 更新笔记的基本格式
vibecopilot memory update --path "目录/标题" --content "新内容"

# 示例：更新开发笔记
vibecopilot memory update \
  --path "dev_notes/开发环境配置" \
  --content "# Python开发环境配置\n\n1. 安装Python 3.9+\n2. 创建虚拟环境\n3. 安装依赖包\n4. 配置IDE\n5. 运行测试"
```

### 4. 删除笔记

删除不再需要的笔记：

```bash
# 删除笔记的基本格式
vibecopilot memory delete --path "目录/标题"

# 示例：删除笔记（带强制确认）
vibecopilot memory delete --path "dev_notes/开发环境配置" --force
```

### 5. 搜索笔记

通过关键词搜索知识库：

```bash
# 搜索笔记的基本格式
vibecopilot memory search --query "搜索关键词"

# 示例：搜索包含"Python"的笔记
vibecopilot memory search --query "Python"
```

### 6. 列出笔记

列出知识库中的笔记：

```bash
# 列出所有笔记
vibecopilot memory list

# 列出特定目录的笔记
vibecopilot memory list --folder "dev_notes"
```

### 7. 同步知识库

同步知识库内容：

```bash
# 同步知识库
vibecopilot memory sync
```

## 高级使用场景

### 使用管道创建笔记

可以通过管道将其他命令的输出作为笔记内容：

```bash
# 将git日志作为笔记保存
git log --oneline -n 10 | vibecopilot memory create --title "最近Git提交" --folder "logs"

# 将命令执行结果保存为笔记
python -m pip list | vibecopilot memory create --title "Python依赖清单" --folder "env_info"
```

### 批量操作

结合shell脚本进行批量操作：

```bash
# 批量导入目录中的markdown文件
for file in docs/*.md; do
  title=$(basename "$file" .md)
  vibecopilot memory create --title "$title" --folder "imported" --content "$(cat $file)"
done
```

### 与其他工具集成

与grep等工具组合使用：

```bash
# 搜索并筛选结果
vibecopilot memory search --query "API" | grep "authentication"
```

## 常见问题解决

1. **无法找到笔记**
   - 检查路径是否正确，包括目录和标题
   - 确认笔记实际存在（使用list命令）

2. **创建笔记失败**
   - 确认Basic Memory项目配置正确
   - 检查目录和标题不包含特殊字符

3. **搜索不返回期望结果**
   - 使用更具体的搜索词
   - 确认知识库已同步（使用sync命令）

## 小技巧

1. 使用`--verbose`参数获取更详细的输出：
   ```bash
   vibecopilot memory list --verbose
   ```

2. 使用标签组织笔记：
   ```bash
   vibecopilot memory create --title "笔记" --folder "目录" --tags "标签1,标签2,标签3"
   ```

3. 设置别名简化命令：
   ```bash
   alias vcm="vibecopilot memory"
   vcm list
   ```
