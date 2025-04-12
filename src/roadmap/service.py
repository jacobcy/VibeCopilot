import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RoadmapService:
    def fix_yaml_file(self, file_path: str, output_path: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
        """
        修复YAML文件格式问题

        使用RoadmapProcessor修复不规范的YAML文件。

        Args:
            file_path: YAML文件路径
            output_path: 输出文件路径，不提供则自动生成
            verbose: 是否启用详细日志

        Returns:
            Dict[str, Any]: 修复结果，包含success字段和message或error字段
        """
        logger.info(f"开始修复YAML文件: {file_path}")

        try:
            from src.parsing.processors.roadmap_processor import RoadmapProcessor

            processor = RoadmapProcessor()

            # 调用处理器的fix_file方法
            success, result = processor.fix_file(file_path, output_path)

            if success:
                logger.info(f"成功修复文件并保存到: {result}")
                return {"success": True, "fixed_path": result, "message": f"成功修复文件并保存到: {result}"}
            else:
                logger.error(f"修复失败: {result}")
                return {"success": False, "error": result, "message": f"修复失败: {result}"}
        except Exception as e:
            error_msg = f"修复过程中出错: {str(e)}"
            logger.exception(error_msg)
            return {"success": False, "error": error_msg}
