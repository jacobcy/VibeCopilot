"""
基于LLM的模板生成器

使用云端LLM服务实现更智能、自然的模板内容生成。
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from src.core.config import get_config
from src.models import Template

from .base_generator import TemplateGenerator

logger = logging.getLogger(__name__)


# 简单的Claude客户端Mock实现
class ClaudeClientMock:
    """模拟Claude API客户端"""

    def __init__(self, api_key: str = "", base_url: str = ""):
        """初始化模拟客户端"""
        self.api_key = api_key
        self.base_url = base_url
        logger.info("初始化模拟Claude客户端")

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000, model: str = "") -> str:
        """模拟内容生成"""
        logger.info(f"模拟调用Claude API，模型：{model}，温度：{temperature}")
        # 简单的模拟实现，返回提示的一部分作为响应
        return f"这是一个由模拟LLM生成的内容。实际使用时，将调用真实的Claude API。\n\n提示示例：{prompt[:100]}..."

    def generate_stream(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000, model: str = ""):
        """模拟流式内容生成"""
        logger.info(f"模拟流式调用Claude API，模型：{model}")
        # 模拟流式生成，返回一个生成器
        yield "这是一个由模拟LLM"
        yield "生成的内容。"
        yield "实际使用时，"
        yield "将调用真实的Claude API。"


class LLMGenerationConfig(BaseModel):
    """LLM生成配置"""

    temperature: float = Field(0.7, description="温度参数，控制生成的创造性")
    max_tokens: int = Field(4000, description="最大生成令牌数")
    model: str = Field("claude-3-opus-20240229", description="使用的LLM模型")
    enhance_context: bool = Field(True, description="是否添加增强上下文")
    use_streaming: bool = Field(False, description="是否使用流式生成")
    add_examples: bool = Field(True, description="是否添加示例")


class LLMTemplateGenerator(TemplateGenerator):
    """基于LLM的模板生成器"""

    def __init__(self, config: Optional[LLMGenerationConfig] = None):
        """
        初始化LLM模板生成器

        Args:
            config: LLM生成配置
        """
        # 获取配置
        self.config = config or LLMGenerationConfig()

        # 初始化模拟Claude客户端
        try:
            api_config = get_config().claude
            api_key = getattr(api_config, "api_key", "mock_key")
            base_url = getattr(api_config, "api_base_url", "https://api.anthropic.com")
        except (AttributeError, Exception) as e:
            logger.warning(f"获取Claude配置失败: {str(e)}，将使用默认值")
            api_key = "mock_key"
            base_url = "https://api.anthropic.com"

        self.client = ClaudeClientMock(
            api_key=api_key,
            base_url=base_url,
        )

    def generate(self, template: Template, variables: Dict[str, Any], output_format: str = "markdown") -> str:
        """
        使用LLM生成内容

        Args:
            template: 模板对象
            variables: 变量值字典
            output_format: 输出格式

        Returns:
            生成的内容
        """
        # 验证变量
        valid, errors = self.validate_variables(template, variables)
        if not valid:
            error_msg = "; ".join(errors)
            logger.warning(f"变量验证警告: {error_msg}")

        # 构建LLM提示
        prompt = self._build_prompt(template, variables, output_format)

        try:
            # 调用LLM API
            if self.config.use_streaming:
                # 流式生成（用于长内容）
                response_text = ""
                for chunk in self.client.generate_stream(
                    prompt, temperature=self.config.temperature, max_tokens=self.config.max_tokens, model=self.config.model
                ):
                    response_text += chunk
                return response_text
            else:
                # 非流式生成
                response = self.client.generate(
                    prompt, temperature=self.config.temperature, max_tokens=self.config.max_tokens, model=self.config.model
                )
                return response

        except Exception as e:
            logger.error(f"LLM生成错误: {str(e)}")
            # 发生错误时，回退到模板内容并应用简单的变量替换
            content = template.content
            for var_name, var_value in variables.items():
                if isinstance(var_value, str):
                    content = content.replace(f"{{{{ {var_name} }}}}", var_value)
            return content

    def validate_variables(self, template: Template, variables: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证变量值

        Args:
            template: 模板对象
            variables: 变量值字典

        Returns:
            (是否验证通过, 错误消息列表)
        """
        errors = []

        # 获取模板变量定义
        template_variables = template.variables if hasattr(template, "variables") else []

        # 检查必需变量
        for var in template_variables:
            var_name = var.name
            is_required = getattr(var, "required", True)

            if is_required and var_name not in variables:
                errors.append(f"缺少必需变量: {var_name}")

        return len(errors) == 0, errors

    def _build_prompt(self, template: Template, variables: Dict[str, Any], output_format: str) -> str:
        """
        构建LLM提示

        Args:
            template: 模板对象
            variables: 变量值字典
            output_format: 输出格式

        Returns:
            LLM提示字符串
        """
        # 准备变量
        prepared_variables = self.prepare_variables(template, variables)

        # 基本提示信息
        prompt = f"""
你是一个专业的内容生成助手，现在需要根据提供的模板和变量生成内容。

## 模板信息
- 名称: {template.name}
- 类型: {template.type}
- 描述: {template.description}

## 模板内容
```
{template.content}
```

## 提供的变量
```json
{json.dumps(prepared_variables, ensure_ascii=False, indent=2)}
```

## 任务
请根据上面的模板和变量，生成一个完整的{output_format}文档。
1. 严格遵循模板的结构和格式
2. 用提供的变量值替换模板中的变量
3. 保持专业、清晰的语言风格
4. 不要添加模板中没有的部分
5. 不要在结果中包含任何提示信息或说明

请直接输出生成的内容，不要添加额外的解释。
"""

        # 如果有示例，添加到提示中
        if self.config.add_examples and hasattr(template, "example") and template.example:
            prompt += f"\n## 示例输出\n```\n{template.example}\n```\n"

        # 如果需要增强上下文，添加更多指导
        if self.config.enhance_context:
            prompt += f"""
## 额外指导
- 确保输出是有效的{output_format}格式
- 变量中的列表应适当展开
- 变量中的对象应正确格式化
- 保持一致的风格和语调
- 生成的内容应该看起来是由人工撰写的，自然流畅
"""

        return prompt
