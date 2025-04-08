import click


@click.group()
def flow():
    """流程会话管理命令，支持创建、启动、停止、查看状态等操作"""
    pass


@flow.command()
@click.option("--name", required=True, help="流程名称")
@click.option("--params", help="流程参数，JSON格式")
@click.option("--verbose", is_flag=True, help="显示详细信息")
def start(name, params, verbose):
    """启动指定流程"""
    click.echo(f"启动流程: {name}，参数: {params}")


@flow.command()
@click.option("--id", required=True, help="流程ID")
@click.option("--force", is_flag=True, help="强制停止流程")
@click.option("--verbose", is_flag=True, help="显示详细信息")
def stop(id, force, verbose):
    """停止指定流程"""
    click.echo(f"停止流程: {id}，强制模式: {force}")


@flow.command()
@click.option("--id", required=True, help="流程ID")
@click.option("--details", is_flag=True, help="显示详细状态信息")
@click.option("--verbose", is_flag=True, help="显示详细信息")
def status(id, details, verbose):
    """查看指定流程状态"""
    click.echo(f"流程状态: {id}，详细信息: {details}")


@flow.command()
@click.option("--id", required=True, help="流程ID")
@click.option("--clean", is_flag=True, help="清理流程缓存")
@click.option("--verbose", is_flag=True, help="显示详细信息")
def restart(id, clean, verbose):
    """重启指定流程"""
    click.echo(f"重启流程: {id}，清理缓存: {clean}")


@flow.command()
@click.option("--all", is_flag=True, help="列出所有流程")
@click.option("--status", help="按状态过滤流程")
@click.option("--format", type=click.Choice(["json", "text"]), default="text", help="输出格式")
@click.option("--verbose", is_flag=True, help="显示详细信息")
def list(all, status, format, verbose):
    """列出流程，支持按状态过滤和多种输出格式"""
    click.echo(f"列出流程，状态: {status}，格式: {format}")
