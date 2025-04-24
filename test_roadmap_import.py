"""
测试路线图导入服务

测试LLM解析结果保存功能，包括各个中间处理步骤
"""

import json
import logging
import os
import time

from src.roadmap.sync.import_service import RoadmapImportService, get_temp_dir

# 配置日志
logging.basicConfig(level=logging.INFO)

# 项目根目录和临时目录常量定义
PROJECT_ROOT = "/Volumes/Cube/Public/VibeCopilot"
TEMP_ROOT = os.path.join(PROJECT_ROOT, "temp")


# 创建一个简单的服务Mock
class RoadmapServiceMock:
    def __init__(self):
        self.storage = self  # 使Mock对象同时作为storage
        self.roadmaps = {}  # 存储路线图数据

    def get_roadmaps(self):
        """获取所有路线图"""
        return [roadmap for roadmap in self.roadmaps.values()]

    def get_roadmap(self, roadmap_id):
        """获取指定ID的路线图"""
        return self.roadmaps.get(roadmap_id)

    def create_roadmap(self, title, description, version, roadmap_id):
        """创建新路线图"""
        print(f"模拟创建路线图: {title} (ID: {roadmap_id})")
        self.roadmaps[roadmap_id] = {"id": roadmap_id, "title": title, "description": description, "version": version, "epics": [], "milestones": []}
        return {"success": True, "roadmap_id": roadmap_id}

    def get_milestones(self, roadmap_id):
        """获取指定路线图的里程碑"""
        roadmap = self.get_roadmap(roadmap_id)
        if roadmap:
            return roadmap.get("milestones", [])
        return []

    def save_roadmap(self, roadmap_id, data):
        """保存路线图数据"""
        print(f"模拟保存路线图: {roadmap_id}")

        # 确保metadata存在
        if "metadata" not in data:
            data["metadata"] = {}

        # 构建路线图数据
        roadmap = {
            "id": roadmap_id,
            "title": data["metadata"].get("title", "未命名路线图"),
            "description": data["metadata"].get("description", ""),
            "version": data["metadata"].get("version", "1.0"),
            "epics": data.get("epics", []),
            "milestones": data.get("milestones", []),
        }

        # 存储路线图
        self.roadmaps[roadmap_id] = roadmap
        return True


def test_import():
    """测试导入功能"""
    # 使用统一的测试数据目录
    test_data_dir = get_temp_dir("test_data", timestamp_subdir=False)
    test_file = os.path.join(test_data_dir, "test_complex_roadmap.yaml")

    # 如果目录不存在，创建它 (这行其实多余，因为get_temp_dir已经创建)
    if not os.path.exists(test_data_dir):
        os.makedirs(test_data_dir, exist_ok=True)

    # 删除旧的测试文件（如果存在），确保使用新的测试数据
    if os.path.exists(test_file):
        try:
            os.remove(test_file)
            print(f"已删除旧的测试文件: {test_file}")
        except Exception as e:
            print(f"无法删除旧的测试文件: {str(e)}")

    # 创建格式不正确的YAML测试文件
    test_content = """
metadata:
  title: 测试路线图
  description: 这是一个用于测试LLM解析的路线图
  version: "1.0"

# 这是一个格式故意不正确的YAML，需要LLM修复
milestones
  - name: 里程碑1
    id: M1
    tasks:
      - name: 任务1.1
        priority: P0
      - name: 任务1.2
        priority: P1

  - name 里程碑2
    id: M2
    tasks
      - name: 任务2.1
        priority: P2
        subtasks:
          - 子任务2.1.1
          - 子任务2.1.2

# 额外的错误格式，确保需要LLM修复
epics
- title: "功能开发"
  stories:
  - title: "用户认证功能"
    不正确的缩进
      tasks:
        - title: "实现登录API"
          priority: critical
"""
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_content)
    print(f"创建测试路线图文件: {test_file}")

    print(f"开始测试导入: {test_file}")
    print(f"文件存在: {os.path.exists(test_file)}")

    # 创建导入服务
    service = RoadmapImportService(RoadmapServiceMock())

    # 执行导入，强制使用LLM解析
    start_time = time.time()
    print("\n开始LLM解析过程...")

    # 尝试导入，如果失败也继续执行
    try:
        result = service.import_from_yaml(test_file, verbose=True, force_llm=True)
        print(f"\n导入结果: {result}")
    except Exception as e:
        print(f"\n导入过程出现异常: {str(e)}")

    end_time = time.time()
    print(f"耗时: {end_time - start_time:.2f}秒")

    # 检查生成的日志目录
    check_log_directories()


def check_log_directories():
    """检查所有日志目录的内容"""
    # 定义需要检查的日志类型目录
    log_types = ["llm_logs", "roadmap_logs", "test_data"]

    for log_type in log_types:
        # 使用统一的路径构建方式
        type_dir = os.path.join(TEMP_ROOT, log_type)
        if not os.path.exists(type_dir):
            print(f"\n日志目录不存在: {type_dir}")
            continue

        print(f"\n{log_type}目录内容:")

        # 列出目录内容
        items = sorted(os.listdir(type_dir))
        if not items:
            print(f"  目录为空")
            continue

        # 列出子目录和文件
        for item in items:
            item_path = os.path.join(type_dir, item)
            if os.path.isdir(item_path):
                print(f"  - 子目录: {item}")
                # 列出子目录内容
                files = sorted(os.listdir(item_path))
                if not files:
                    print("    目录为空")
                else:
                    for file in files:
                        file_path = os.path.join(item_path, file)
                        file_size = os.path.getsize(file_path)
                        print(f"    - 文件: {file} ({file_size} 字节)")

                        # 显示重要日志文件的内容预览
                        if file.startswith("request_") or file.startswith("response_"):
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    content = f.read(500)  # 只读取前500个字符
                                preview = content[:100] + "..." if len(content) > 100 else content
                                print(f"      内容预览: {preview}")
                            except Exception as e:
                                print(f"      内容读取失败: {str(e)}")
            else:
                # 文件
                file_size = os.path.getsize(item_path)
                print(f"  - 文件: {item} ({file_size} 字节)")


if __name__ == "__main__":
    test_import()
