# AI 项目分析与路线图更新指南

本指南专门为 AI 系统设计，用于指导如何分析项目状态并更新路线图进度。

## 项目分析流程

### 1. 获取项目信息

```python
# 获取项目基本信息
python scripts/github/get_project_info.py \
  --owner {owner} \
  --repo {repo} \
  --project-number {number}

# 获取所有任务列表
python scripts/github/list_tasks.py \
  --format json \
  --output project_tasks.json
```

### 2. 分析维度

#### 进度分析
- 已完成任务数量和比例
- 各状态任务分布
- 预计完成时间偏差

#### 质量分析
- PR 合并率
- 代码审查评论数量
- 测试覆盖率变化

#### 风险分析
- 阻塞任务数量
- 延期任务比例
- 依赖项状态

### 3. 数据结构规范

```typescript
interface ProjectAnalysis {
    progress: {
        completed: number;
        total: number;
        completion_rate: number;
        status_distribution: {
            [status: string]: number;
        };
    };
    quality: {
        pr_merge_rate: number;
        review_comments_avg: number;
        test_coverage: number;
    };
    risks: {
        blocked_tasks: number;
        delayed_tasks: number;
        dependencies_status: {
            [dependency: string]: "healthy" | "at_risk" | "blocked";
        };
    };
}
```

## 路线图更新流程

### 1. 生成分析报告

```bash
python scripts/github/analyze_project.py \
  --metrics "progress,quality,risks" \
  --output analysis.json
```

### 2. 更新任务状态

```bash
python scripts/github/bulk_update_tasks.py \
  --input updates.json \
  --auto-adjust-timeline true
```

### 3. 调整时间线

```bash
python scripts/github/adjust_timeline.py \
  --based-on-analysis analysis.json \
  --update-milestones true
```

## 决策规则

### 1. 进度评估规则

- **正常进度**：完成率 >= 计划进度 - 5%
- **需要关注**：完成率在计划进度 -5% 到 -15% 之间
- **需要干预**：完成率 < 计划进度 - 15%

### 2. 风险等级判定

```python
def assess_risk_level(metrics):
    risk_score = 0

    # 延期任务比例
    if metrics.delayed_rate > 0.2:
        risk_score += 2
    elif metrics.delayed_rate > 0.1:
        risk_score += 1

    # 阻塞任务数量
    if metrics.blocked_tasks > 5:
        risk_score += 2
    elif metrics.blocked_tasks > 2:
        risk_score += 1

    # 返回风险等级
    return "HIGH" if risk_score >= 3 else "MEDIUM" if risk_score >= 1 else "LOW"
```

### 3. 自动调整策略

- **轻微延期** (<1周)：自动调整任务时间线
- **中度延期** (1-2周)：提示人工审查
- **严重延期** (>2周)：要求项目负责人介入

## 更新执行

### 1. 准备更新数据

```python
def prepare_updates(analysis):
    updates = {
        "timeline_adjustments": [],
        "status_changes": [],
        "risk_alerts": []
    }

    # 基于分析结果生成更新
    for task in analysis.tasks:
        if needs_adjustment(task):
            updates["timeline_adjustments"].append({
                "task_id": task.id,
                "new_due_date": calculate_new_due_date(task)
            })

    return updates
```

### 2. 执行更新

```bash
# 应用更新
python scripts/github/apply_updates.py \
  --updates-file updates.json \
  --dry-run false  # 设置为 true 可以预览更改

# 生成更新报告
python scripts/github/generate_update_report.py \
  --updates-file updates.json \
  --format markdown
```

### 3. 验证更新

```bash
# 验证更新结果
python scripts/github/verify_updates.py \
  --updates-file updates.json \
  --generate-diff true
```

## 注意事项

1. **数据一致性**
   - 每次更新前备份当前状态
   - 验证更新是否完整应用
   - 保持更新原子性

2. **更新限制**
   - 单次最大更新任务数：50
   - 时间调整范围：±30天
   - API 调用频率限制

3. **异常处理**
   - 记录所有失败的更新
   - 提供回滚机制
   - 保存详细的错误日志

## 模板

### 1. 分析报告模板

```markdown
# 项目分析报告

## 总体状况
- 完成度：{completion_rate}%
- 风险等级：{risk_level}
- 健康指数：{health_score}

## 需要注意
1. {key_point_1}
2. {key_point_2}
3. {key_point_3}

## 建议操作
1. {recommendation_1}
2. {recommendation_2}
3. {recommendation_3}
```

### 2. 更新通知模板

```markdown
# 路线图更新通知

## 更新内容
- 调整了 {adjusted_tasks_count} 个任务的时间线
- 更新了 {status_updates_count} 个任务的状态
- 添加了 {new_tasks_count} 个新任务

## 主要变更
1. {major_change_1}
2. {major_change_2}
3. {major_change_3}

## 后续操作
- {next_step_1}
- {next_step_2}
- {next_step_3}
```

## API 参考

### 1. 分析 API
```python
analyze_project(project_id: str) -> ProjectAnalysis
```

### 2. 更新 API
```python
update_roadmap(
    project_id: str,
    updates: RoadmapUpdates,
    options: UpdateOptions
) -> UpdateResult
```

### 3. 验证 API
```python
verify_updates(
    project_id: str,
    update_id: str
) -> VerificationResult
```

---

本指南提供了 AI 系统进行项目分析和路线图更新所需的所有必要信息。通过遵循这些规范和流程，AI 可以准确评估项目状态并做出合适的更新决策。
