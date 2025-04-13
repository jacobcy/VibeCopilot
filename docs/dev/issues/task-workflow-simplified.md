# 具体的实现方案

1. 数据模型（已存在，无需修改）：

```python
# src/models/db/task.py
class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True)
    title = Column(String)
    status = Column(String)
    story_id = Column(String, nullable=True)
    github_issue = Column(String, nullable=True)
    current_session_id = Column(String, nullable=True)

# src/models/db/flow_session.py
class FlowSession(Base):
    __tablename__ = 'flow_sessions'
    id = Column(String, primary_key=True)
    flow_type = Column(String)
    status = Column(String)
    task_id = Column(String, ForeignKey('tasks.id'))
    is_current = Column(Boolean, default=False)
```

2. 需要修改的文件：

```
src/
├── cli/commands/task/
│   ├── task_click.py           # 更新命令实现
│   └── core/
│       ├── create.py           # 更新创建任务逻辑
│       ├── update.py           # 更新更新任务逻辑
│       └── link.py             # 重写link命令逻辑
├── services/
│   └── task_service.py         # 添加新的服务方法
└── health/config/commands/
    └── task_commands.yaml      # 更新命令配置
```

3. 具体修改内容：

a. 更新 `task_commands.yaml`：
```yaml
"task create":
  # ... 保持原有选项 ...
  subcommands:
    "--link-story":
      description: "关联到Story"
    "--link-github":
      description: "关联到GitHub Issue (格式: owner/repo#number)"
    "--flow":
      description: "创建并关联工作流会话"
      short: "-f"
      values: ["dev", "review", "deploy"]

"task update":
  # ... 保持原有选项 ...
  subcommands:
    "--link-story":
      description: "关联到Story"
    "--link-github":
      description: "关联到GitHub Issue (格式: owner/repo#number)"
    "--unlink":
      description: "取消关联"
      values: ["story", "github"]

"task link":
  description: "管理任务的工作流会话"
  arguments:
    - name: "task_id"
      description: "任务ID，不指定则使用当前任务"
      required: false
  subcommands:
    "--flow":
      description: "创建新的工作流会话"
      short: "-f"
      values: ["dev", "review", "deploy"]
    "--session":
      description: "关联到已存在的会话"
      short: "-s"
```

b. 扩展 `TaskService`：
```python
def get_current_task(self) -> Optional[Dict[str, Any]]:
    """获取当前任务"""
    try:
        task = self._db_service.task_repo.get_current_task()
        return task.to_dict() if task else None
    except Exception as e:
        logger.error(f"获取当前任务失败: {e}")
        return None

def set_current_task(self, task_id: str) -> bool:
    """设置当前任务"""
    try:
        return self._db_service.task_repo.set_current_task(task_id)
    except Exception as e:
        logger.error(f"设置当前任务失败: {e}")
        return False

def link_to_flow_session(self, task_id: str, flow_type: str = None, session_id: str = None) -> Optional[Dict[str, Any]]:
    """关联任务到工作流会话"""
    try:
        if flow_type:
            # 创建新会话
            session = FlowSessionManager.create_session(flow_type, task_id)
        elif session_id:
            # 关联到已有会话
            session = FlowSessionManager.get_session(session_id)
            if session:
                session = FlowSessionManager.link_task(session.id, task_id)

        if session:
            # 更新任务的当前会话
            self._db_service.task_repo.update_task(task_id, {
                "current_session_id": session.id
            })
            return session.to_dict()
        return None
    except Exception as e:
        logger.error(f"关联任务到工作流会话失败: {e}")
        return None
```

c. 更新 `TaskRepository`：
```python
def get_current_task(self) -> Optional[Task]:
    """获取当前任务"""
    return self.session.query(Task).filter(Task.is_current == True).first()

def set_current_task(self, task_id: str) -> bool:
    """设置当前任务"""
    try:
        # 清除其他任务的当前状态
        self.session.query(Task).filter(Task.is_current == True).update(
            {"is_current": False}
        )
        # 设置新的当前任务
        task = self.get_by_id(task_id)
        if task:
            task.is_current = True
            self.session.commit()
            return True
        return False
    except Exception as e:
        self.session.rollback()
        logger.error(f"设置当前任务失败: {e}")
        return False
```

4. 工作流切换时的任务联动：

在 `WorkflowStatusProvider` 中添加：
```python
def switch_session(self, session_id: str) -> Dict:
    """切换当前工作流会话"""
    session = FlowSessionManager.get_session(session_id)
    if not session:
        return {"error": "会话不存在"}

    # 更新会话状态
    FlowSessionManager.set_current_session(session_id)

    # 自动切换关联的任务
    if session.task_id:
        task_service = TaskService()
        task_service.set_current_task(session.task_id)

    return {
        "status": "success",
        "current_session": session_id,
        "current_task": session.task_id
    }
```
