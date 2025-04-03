"""
数据库迁移命令模块

提供从旧数据库架构迁移到新统一数据库架构的功能。
"""

import logging
import os
import json
import uuid
from typing import Any, Dict, List, Optional

from src.cli.base_command import BaseCommand
from src.db.service import DatabaseService
from src.roadmap.service import DatabaseService as OldDatabaseService
from src.roadmap.models import Epic as OldEpic, Story as OldStory, Task as OldTask, Label as OldLabel
from src.rule_templates.core.template_manager import TemplateManager
from src.rule_templates.repositories.template_repository import FileSystemTemplateRepository

logger = logging.getLogger(__name__)


class DatabaseMigrateCommand(BaseCommand):
    """数据库迁移命令处理器"""

    def __init__(self):
        """初始化数据库迁移命令"""
        super().__init__(name="db-migrate", description="将现有数据迁移到统一数据库")
        
        # 注册参数
        self.register_args(
            required=["action"],
            optional={
                "source": None,      # 源数据库路径
                "target": None,      # 目标数据库路径
                "type": "all",       # 迁移类型(roadmap/template/all)
                "dry_run": False,    # 是否只模拟运行
                "force": False,      # 是否强制运行
            },
        )
        
        # 项目路径
        self.project_path = os.environ.get("PROJECT_ROOT", os.getcwd())
        
        # 数据库服务
        self.db_service = None
        self.old_db_service = None
        self.template_manager = None
    
    def _initialize_services(self, args: Dict[str, Any]) -> None:
        """初始化数据库服务
        
        Args:
            args: 命令参数
        """
        # 初始化新数据库服务
        target_db_path = args.get("target")
        if not target_db_path:
            target_db_path = os.path.join(self.project_path, ".ai", "vibecopilot.db")
        self.db_service = DatabaseService(target_db_path)
        
        # 初始化旧数据库服务
        source_db_path = args.get("source")
        if not source_db_path:
            source_db_path = os.path.join(self.project_path, ".ai", "database.sqlite")
        self.old_db_service = OldDatabaseService(source_db_path)
        
        # 初始化模板管理器
        templates_dir = os.path.join(self.project_path, "templates", "rule_templates")
        storage_adapter = FileSystemTemplateRepository(templates_dir)
        self.template_manager = TemplateManager(templates_dir, storage_adapter)

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据库迁移命令
        
        Args:
            args: 命令参数
                - action: 要执行的操作(migrate/check)
                - source: 源数据库路径(可选)
                - target: 目标数据库路径(可选)
                - type: 迁移类型(roadmap/template/all)(可选)
                - dry_run: 是否只模拟运行(可选)
                - force: 是否强制运行(可选)
                
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 初始化服务
        self._initialize_services(args)
        
        # 获取参数
        action = args["action"]
        migration_type = args.get("type", "all")
        dry_run = args.get("dry_run", False)
        
        # 根据操作类型执行不同逻辑
        if action == "check":
            return self._check_migration(migration_type)
        elif action == "migrate":
            return self._migrate_data(migration_type, dry_run)
        else:
            return {"success": False, "error": f"未知操作: {action}"}
    
    def _check_migration(self, migration_type: str) -> Dict[str, Any]:
        """检查迁移状态
        
        Args:
            migration_type: 迁移类型
            
        Returns:
            Dict[str, Any]: 检查结果
        """
        result = {"success": True, "data": {}}
        
        if migration_type in ["roadmap", "all"]:
            # 检查路线图数据
            try:
                old_epics = self.old_db_service.list_epics()
                old_stories = self.old_db_service.list_stories()
                old_tasks = self.old_db_service.list_tasks()
                old_labels = self.old_db_service.list_labels()
                
                result["data"]["roadmap"] = {
                    "source": {
                        "epics": len(old_epics),
                        "stories": len(old_stories),
                        "tasks": len(old_tasks),
                        "labels": len(old_labels)
                    }
                }
            except Exception as e:
                logger.error(f"检查路线图源数据失败: {e}")
                result["data"]["roadmap"] = {"error": str(e)}
        
        if migration_type in ["template", "all"]:
            # 检查模板数据
            try:
                old_templates = self.template_manager.get_all_templates()
                
                result["data"]["template"] = {
                    "source": {
                        "templates": len(old_templates)
                    }
                }
            except Exception as e:
                logger.error(f"检查模板源数据失败: {e}")
                result["data"]["template"] = {"error": str(e)}
        
        return result
    
    def _migrate_data(self, migration_type: str, dry_run: bool) -> Dict[str, Any]:
        """迁移数据
        
        Args:
            migration_type: 迁移类型
            dry_run: 是否只模拟运行
            
        Returns:
            Dict[str, Any]: 迁移结果
        """
        result = {"success": True, "migrated": {}}
        
        if migration_type in ["roadmap", "all"]:
            # 迁移路线图数据
            roadmap_result = self._migrate_roadmap_data(dry_run)
            result["migrated"]["roadmap"] = roadmap_result
            
            if not roadmap_result.get("success", False):
                result["success"] = False
        
        if migration_type in ["template", "all"]:
            # 迁移模板数据
            template_result = self._migrate_template_data(dry_run)
            result["migrated"]["template"] = template_result
            
            if not template_result.get("success", False):
                result["success"] = False
        
        return result
    
    def _migrate_roadmap_data(self, dry_run: bool) -> Dict[str, Any]:
        """迁移路线图数据
        
        Args:
            dry_run: 是否只模拟运行
            
        Returns:
            Dict[str, Any]: 迁移结果
        """
        try:
            # 获取旧数据
            old_epics = self.old_db_service.list_epics()
            old_stories = self.old_db_service.list_stories()
            old_tasks = self.old_db_service.list_tasks()
            old_labels = self.old_db_service.list_labels()
            
            migrated_counts = {
                "epics": 0,
                "stories": 0,
                "tasks": 0,
                "labels": 0
            }
            
            if not dry_run:
                # 先迁移标签
                for label_data in old_labels:
                    self.db_service.create_label(label_data)
                    migrated_counts["labels"] += 1
                
                # 迁移Epic
                for epic_data in old_epics:
                    self.db_service.create_epic(epic_data)
                    migrated_counts["epics"] += 1
                
                # 迁移Story
                for story_data in old_stories:
                    self.db_service.create_story(story_data)
                    migrated_counts["stories"] += 1
                
                # 迁移Task
                for task_data in old_tasks:
                    # 处理标签关系
                    labels = task_data.pop("labels", [])
                    
                    # 创建任务
                    task = self.db_service.create_task(task_data)
                    
                    # 添加标签关系
                    if labels and task:
                        for label_name in labels:
                            # 获取标签ID
                            label = next((l for l in old_labels if l["name"] == label_name), None)
                            if label:
                                # 添加任务标签关系
                                with self.db_service.get_session() as session:
                                    task_repo = self.db_service.task_repo.__class__(session)
                                    task_repo.add_label(task["id"], label["id"])
                    
                    migrated_counts["tasks"] += 1
            
            return {
                "success": True,
                "source_counts": {
                    "epics": len(old_epics),
                    "stories": len(old_stories),
                    "tasks": len(old_tasks),
                    "labels": len(old_labels)
                },
                "migrated_counts": migrated_counts,
                "dry_run": dry_run
            }
        except Exception as e:
            logger.error(f"迁移路线图数据失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _migrate_template_data(self, dry_run: bool) -> Dict[str, Any]:
        """迁移模板数据
        
        Args:
            dry_run: 是否只模拟运行
            
        Returns:
            Dict[str, Any]: 迁移结果
        """
        try:
            # 获取旧数据
            old_templates = self.template_manager.get_all_templates()
            
            migrated_counts = {
                "templates": 0,
                "variables": 0
            }
            
            if not dry_run:
                # 迁移模板
                for template in old_templates:
                    # 转换为字典
                    template_dict = template.dict()
                    
                    # 创建模板
                    self.db_service.create_template(template_dict)
                    migrated_counts["templates"] += 1
                    
                    # 统计变量数量
                    migrated_counts["variables"] += len(template.variables)
            
            return {
                "success": True,
                "source_counts": {
                    "templates": len(old_templates)
                },
                "migrated_counts": migrated_counts,
                "dry_run": dry_run
            }
        except Exception as e:
            logger.error(f"迁移模板数据失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 命令实例
command = DatabaseMigrateCommand()