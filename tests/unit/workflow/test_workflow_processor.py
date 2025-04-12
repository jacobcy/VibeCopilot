import pytest

from src.parsing.processors.workflow_processor import WorkflowProcessor


@pytest.mark.asyncio
async def test_parse_workflow():
    """测试工作流解析"""
    # 创建测试工作流内容
    workflow_content = """
    name: 测试工作流
    description: 这是一个测试工作流
    stages:
      - name: 开始
        type: start
        next: 处理
      - name: 处理
        type: task
        next: 结束
      - name: 结束
        type: end
    """

    # 初始化处理器
    processor = WorkflowProcessor()

    # 解析工作流
    result = await processor.parse_workflow(workflow_content)

    # 验证结果
    assert result is not None
    assert result["name"] == "测试工作流"
    assert result["description"] == "这是一个测试工作流"
    assert len(result["stages"]) == 3

    # 验证阶段
    stages = result["stages"]
    assert stages[0]["name"] == "开始"
    assert stages[0]["type"] == "start"
    assert stages[1]["name"] == "处理"
    assert stages[1]["type"] == "task"
    assert stages[2]["name"] == "结束"
    assert stages[2]["type"] == "end"


@pytest.mark.asyncio
async def test_parse_invalid_workflow():
    """测试解析无效的工作流内容"""
    # 创建无效的工作流内容
    invalid_content = "invalid workflow content"

    # 初始化处理器
    processor = WorkflowProcessor()

    # 解析工作流
    result = await processor.parse_workflow(invalid_content)

    # 验证结果为None
    assert result is None
