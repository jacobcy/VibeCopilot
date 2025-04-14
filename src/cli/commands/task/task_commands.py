@task.command(name="create")
@click.argument("title", required=True)
@click.option("--desc", "-d", help="任务描述")
@click.option("--priority", "-p", type=click.Choice(["low", "medium", "high"]), default="medium", help="任务优先级")
@click.option("--status", "-s", type=click.Choice(["todo", "in_progress", "done"]), default="todo", help="任务状态")
@click.option("--flow", "-f", help="要关联的工作流ID，将自动创建工作流会话")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def create_task(title: str, description: str, priority: str, status: str, flow: str, verbose: bool):
    """创建新任务

    可选择关联工作流，将自动创建对应的工作流会话。

    示例:
        vc task create "实现登录功能" -d "开发用户登录模块" -p high
        vc task create "重构数据模型" --flow dev  # 创建任务并关联开发工作流
    """
    try:
        task_service = TaskService()
        task_data = {"title": title, "description": description, "priority": priority, "status": status}

        if flow:
            # 如果指定了工作流，使用create_task_with_flow
            task = task_service.create_task_with_flow(task_data, flow)
            if not task:
                click.echo("创建任务失败", err=True)
                return

            click.echo(f"✅ 已创建任务: {task['title']}")
            click.echo(f"任务ID: {task['id']}")
            click.echo(f"已关联工作流会话: {task['flow_session']['id']}")

            if verbose:
                click.echo("\n会话详情:")
                click.echo(f"- 名称: {task['flow_session']['name']}")
                click.echo(f"- 状态: {task['flow_session']['status']}")
        else:
            # 常规任务创建
            task = task_service.create_task(task_data)
            if not task:
                click.echo("创建任务失败", err=True)
                return

            click.echo(f"✅ 已创建任务: {task['title']}")
            click.echo(f"任务ID: {task['id']}")

    except Exception as e:
        click.echo(f"创建任务时出错: {str(e)}", err=True)
