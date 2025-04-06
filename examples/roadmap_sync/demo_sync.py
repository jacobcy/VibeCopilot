#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub同步演示脚本

提供路线图与GitHub同步的简化演示代码
包含多种同步选项和使用场景
"""

import argparse
import logging
import os

import yaml

from src.roadmap.service import RoadmapService

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_env_vars(mock=True):
    """设置环境变量"""
    # 启用模拟模式避免实际API调用
    if mock:
        os.environ["MOCK_SYNC"] = "true"
        print("✅ 已启用模拟模式 (MOCK_SYNC=true)")
    else:
        if "MOCK_SYNC" in os.environ:
            del os.environ["MOCK_SYNC"]
        print("⚠️ 已禁用模拟模式 - 将进行实际GitHub API调用")

    # 检查必要的环境变量
    missing_vars = []
    for var in ["GITHUB_TOKEN", "GITHUB_OWNER", "GITHUB_REPO"]:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"⚠️ 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请设置这些环境变量或使用模拟模式")
        return False

    return True


def import_roadmap(service, roadmap_id, yaml_path):
    """导入路线图数据"""
    print(f"\n📥 从YAML导入路线图数据...")
    print(f"- YAML文件: {yaml_path}")
    print(f"- 路线图ID: {roadmap_id}")

    try:
        result = service.import_from_yaml(yaml_path, roadmap_id)
        if result.get("success", False):
            print(f"✅ 导入成功")
            return True
        else:
            print(f"❌ 导入失败: {result.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 导入出错: {str(e)}")
        return False


def update_theme(service, roadmap_id, theme_value, yaml_path):
    """更新路线图Theme值"""
    print(f"\n🔄 更新路线图Theme字段...")
    print(f"- 路线图ID: {roadmap_id}")
    print(f"- 新Theme值: {theme_value}")

    try:
        # 读取原YAML文件
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # 更新theme值
        data["theme"] = theme_value

        # 创建临时文件
        import tempfile

        temp_fd, temp_path = tempfile.mkstemp(suffix=".yaml")
        os.close(temp_fd)

        # 写入更新后的数据
        with open(temp_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)

        # 重新导入
        result = service.import_from_yaml(temp_path, roadmap_id)

        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if result.get("success", False):
            print(f"✅ Theme更新成功")
            return True
        else:
            print(f"❌ Theme更新失败: {result.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ Theme更新出错: {str(e)}")
        return False


def sync_to_github(service, roadmap_id):
    """同步路线图到GitHub"""
    print(f"\n📤 同步路线图到GitHub...")
    print(f"- 路线图ID: {roadmap_id}")

    try:
        sync_result = service.sync_to_github(roadmap_id)
        if sync_result.get("success", False):
            print(f"✅ 同步成功!")
            print(f"- 路线图: {sync_result.get('roadmap_name')}")
            print(f"- GitHub项目: {sync_result.get('github_project')}")

            # 显示统计信息
            stats = sync_result.get("stats", {})
            print(f"- 里程碑: {stats.get('milestones_synced', 0)}个")
            print(f"- 史诗: {stats.get('epics_synced', 0)}个")
            print(f"- 新建问题: {stats.get('issues_created', 0)}个")
            print(f"- 更新问题: {stats.get('issues_updated', 0)}个")

            # 显示额外注释
            if sync_result.get("note"):
                print(f"- 注意: {sync_result.get('note')}")

            return True
        else:
            print(f"❌ 同步失败: {sync_result.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 同步出错: {str(e)}")
        return False


def sync_from_github(service, roadmap_id):
    """从GitHub同步状态到路线图"""
    print(f"\n📥 从GitHub同步状态到路线图...")
    print(f"- 路线图ID: {roadmap_id}")

    try:
        status_result = service.sync_from_github(roadmap_id)
        if status_result.get("success", False):
            print(f"✅ 状态同步成功!")
            stats = status_result.get("stats", {})
            print(f"- 更新任务: {stats.get('tasks_updated', 0)}个")
            print(f"- 更新里程碑: {stats.get('milestones_updated', 0)}个")

            if status_result.get("note"):
                print(f"- 注意: {status_result.get('note')}")

            return True
        else:
            print(f"❌ 状态同步失败: {status_result.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 状态同步出错: {str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="路线图GitHub同步演示")
    parser.add_argument("--roadmap-id", default="roadmap-rule-engine-roadmap", help="路线图ID")
    parser.add_argument(
        "--yaml-path", default=".ai/roadmap/rule_engine_roadmap.yaml", help="YAML文件路径"
    )
    parser.add_argument("--theme", default="github-project-1", help="GitHub项目ID/Theme值")
    parser.add_argument("--no-mock", action="store_true", help="禁用模拟模式，执行实际API调用")
    parser.add_argument("--import-only", action="store_true", help="仅导入路线图数据")
    parser.add_argument("--sync-only", action="store_true", help="仅执行同步操作")

    args = parser.parse_args()

    # 设置环境变量
    use_mock = not args.no_mock
    if not setup_env_vars(mock=use_mock):
        if use_mock:
            print("继续使用模拟模式...")
        else:
            print("❌ 环境变量缺失，终止执行")
            return

    # 初始化路线图服务
    print("初始化路线图服务...")
    roadmap_service = RoadmapService()

    # 设置活跃路线图（如果需要导入，请先导入）
    if args.import_only or not args.sync_only:
        # 导入路线图
        if not import_roadmap(roadmap_service, args.roadmap_id, args.yaml_path):
            print("⚠️ 导入失败，但将继续尝试后续步骤")

        # 更新theme
        if not update_theme(roadmap_service, args.roadmap_id, args.theme, args.yaml_path):
            print("⚠️ Theme更新失败，但将继续尝试后续步骤")

    # 设置活跃路线图
    try:
        roadmap_service.set_active_roadmap(args.roadmap_id)
        print(f"✅ 已设置活跃路线图: {args.roadmap_id}")
    except Exception as e:
        print(f"❌ 设置活跃路线图失败: {str(e)}")
        return

    # 执行同步
    if args.import_only:
        print("仅执行导入操作，跳过同步步骤")
    else:
        # 同步到GitHub
        if sync_to_github(roadmap_service, args.roadmap_id):
            # 从GitHub同步状态
            sync_from_github(roadmap_service, args.roadmap_id)

    print("\n✨ 演示完成!")


if __name__ == "__main__":
    main()
