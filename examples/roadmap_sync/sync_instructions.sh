#!/bin/bash

# GitHub同步指南脚本
# 提供VibeCopilot路线图与GitHub同步的命令示例

# 设置环境变量
echo "设置GitHub环境变量..."
export GITHUB_TOKEN="your_personal_access_token"  # 替换为实际token
export GITHUB_OWNER="your_github_username"        # 替换为实际用户名/组织名
export GITHUB_REPO="your_repository_name"         # 替换为实际仓库名
export MOCK_SYNC="true"                           # 开发测试模式，避免真实API调用

# 导入路线图
echo "1. 导入路线图数据..."
python -c "from src.roadmap.service import RoadmapService; \
           service = RoadmapService(); \
           result = service.import_from_yaml('.ai/roadmap/rule_engine_roadmap.yaml', 'roadmap-rule-engine-roadmap'); \
           print(f'导入结果: {result}')"

# 更新Theme
echo "2. 更新路线图Theme字段..."
python update_theme_correct.py

# 执行同步
echo "3. 执行GitHub同步..."
python final_github_sync.py

echo "完成! 请查看以上命令输出，确认同步状态。"
echo "注意: 真实同步时请设置 MOCK_SYNC=false 并确保GitHub令牌有足够权限"
