"""
路线图验证处理器模块

提供路线图YAML文件验证的处理逻辑。
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console

from src.validation.roadmap_validation import RoadmapValidator

console = Console()
logger = logging.getLogger(__name__)


class RoadmapValidateHandlers:
    """路线图验证处理器"""

    @staticmethod
    async def handle_validate_command(args: Dict[str, Any], service) -> Dict[str, Any]:
        """处理验证命令

        Args:
            args: 命令参数
            service: 路线图服务实例

        Returns:
            Dict[str, Any]: 处理结果
        """
        source = args["source"]
        fix = args.get("fix", False)
        output = args.get("output")
        template = args.get("template")
        verbose = args.get("verbose", False)
        import_data = args.get("import_data", False)
        roadmap_id = args.get("roadmap_id")

        try:
            # 创建验证器
            validator = RoadmapValidator()

            # 验证文件
            is_valid, warnings, errors = validator.validate_file(source)

            # 准备结果
            result = {"success": is_valid, "warnings": warnings, "errors": errors, "source": source}

            # 如果验证通过且需要导入
            if is_valid and import_data:
                import_result = await RoadmapValidateHandlers.handle_import(service, source, roadmap_id, verbose)
                result.update(import_result)

            # 如果需要修复
            if fix and (not is_valid or warnings):
                fix_result = await RoadmapValidateHandlers.handle_fix(service, source, output, verbose)
                result.update(fix_result)

                # 如果修复成功且需要导入
                if fix_result.get("success") and import_data:
                    fixed_path = fix_result.get("fixed_path")
                    if fixed_path:
                        import_result = await RoadmapValidateHandlers.handle_import(service, fixed_path, roadmap_id, verbose)
                        result.update(import_result)

            return result

        except Exception as e:
            logger.exception("验证过程出错")
            return {"success": False, "error": str(e), "source": source}

    @staticmethod
    async def handle_fix(service, source: str, output: Optional[str], verbose: bool) -> Dict[str, Any]:
        """处理修复

        Args:
            service: 路线图服务实例
            source: 源文件路径
            output: 输出文件路径
            verbose: 是否显示详细信息

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 确定输出路径
            if not output:
                basename = os.path.basename(source)
                name, ext = os.path.splitext(basename)
                output = f"{os.path.dirname(source)}/{name}_fixed{ext}"

            # 使用服务修复文件
            result = await service.fix_yaml_file(source, output, verbose=verbose)

            if result.get("success"):
                return {"success": True, "fixed": True, "fixed_path": result.get("fixed_path"), "message": f"已修复并保存到: {result.get('fixed_path')}"}
            else:
                return {"success": False, "fixed": False, "error": result.get("error", "修复失败"), "message": f"修复失败: {result.get('error', '未知错误')}"}

        except Exception as e:
            logger.exception("修复过程出错")
            return {"success": False, "fixed": False, "error": str(e), "message": f"修复过程出错: {str(e)}"}

    @staticmethod
    async def handle_import(service, file_path: str, roadmap_id: Optional[str], verbose: bool) -> Dict[str, Any]:
        """处理导入

        Args:
            service: 路线图服务实例
            file_path: 文件路径
            roadmap_id: 路线图ID
            verbose: 是否显示详细信息

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            result = await service.import_from_yaml(file_path, roadmap_id, verbose)

            if result.get("success"):
                return {
                    "success": True,
                    "imported": True,
                    "roadmap_id": result.get("roadmap_id"),
                    "message": f"导入成功: 路线图ID {result.get('roadmap_id')}",
                }
            else:
                return {"success": False, "imported": False, "error": result.get("error", "导入失败"), "message": f"导入失败: {result.get('error', '未知错误')}"}

        except Exception as e:
            logger.exception("导入过程出错")
            return {"success": False, "imported": False, "error": str(e), "message": f"导入过程出错: {str(e)}"}
