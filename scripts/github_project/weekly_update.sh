#!/bin/bash

# GitHub项目每周自动分析和更新脚本
# 用于定期运行项目分析并更新路线图

# 设置工作目录为项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$PROJECT_ROOT"

# 读取.env文件
if [ -f .env ]; then
  echo "加载.env配置文件"
  export $(grep -v '^#' .env | xargs)
fi

# 检查必要的环境变量
if [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_OWNER" ] || [ -z "$GITHUB_REPO" ] || [ -z "$GITHUB_PROJECT_NUMBER" ]; then
  echo "错误: 缺少必要的环境变量，请确保设置了以下变量:"
  echo "- GITHUB_TOKEN"
  echo "- GITHUB_OWNER"
  echo "- GITHUB_REPO"
  echo "- GITHUB_PROJECT_NUMBER"
  exit 1
fi

# 创建输出目录
OUTPUT_DIR="$PROJECT_ROOT/reports/github"
mkdir -p "$OUTPUT_DIR"

# 设置日期
DATE_TAG=$(date +"%Y%m%d")
ANALYSIS_FILE="$OUTPUT_DIR/analysis_$DATE_TAG.json"
REPORT_FILE="$OUTPUT_DIR/report_$DATE_TAG.md"
ADJUSTMENT_FILE="$OUTPUT_DIR/adjustment_$DATE_TAG.json"

echo "===== 开始项目周报自动分析 ====="
echo "日期: $(date)"
echo "项目: $GITHUB_OWNER/$GITHUB_REPO 项目 #$GITHUB_PROJECT_NUMBER"
echo "分析结果将保存到: $ANALYSIS_FILE"
echo "报告将保存到: $REPORT_FILE"
echo "调整结果将保存到: $ADJUSTMENT_FILE"

# 步骤1: 运行项目分析
echo -e "\n1. 执行项目分析..."
python scripts/github/analyze_project.py --metrics "progress,quality,risks" --output "$ANALYSIS_FILE" --format json

if [ $? -ne 0 ]; then
  echo "错误: 项目分析失败"
  exit 1
fi

# 步骤2: 生成Markdown报告
echo -e "\n2. 生成分析报告..."
python -c "
import sys, json, os
sys.path.insert(0, os.path.abspath('$PROJECT_ROOT'))
from src.github.projects import ProjectAnalyzer
with open('$ANALYSIS_FILE', 'r', encoding='utf-8') as f:
    analysis = json.load(f)
analyzer = ProjectAnalyzer()
report = analyzer.generate_report(analysis, format_type='markdown')
with open('$REPORT_FILE', 'w', encoding='utf-8') as f:
    f.write(report)
print('报告生成完成: $REPORT_FILE')
"

if [ $? -ne 0 ]; then
  echo "错误: 报告生成失败"
  exit 1
fi

# 步骤3: 调整项目时间线
echo -e "\n3. 调整项目时间线..."
python scripts/github/adjust_timeline.py --based-on-analysis "$ANALYSIS_FILE" --output "$ADJUSTMENT_FILE" --update-milestones "false"

if [ $? -ne 0 ]; then
  echo "错误: 时间线调整失败"
  exit 1
fi

# 步骤4: 生成调整建议
echo -e "\n4. 生成调整建议..."
SUGGESTIONS_FILE="$OUTPUT_DIR/suggestions_$DATE_TAG.md"

echo "# 项目调整建议" > "$SUGGESTIONS_FILE"
echo "" >> "$SUGGESTIONS_FILE"
echo "## 自动生成的时间线调整" >> "$SUGGESTIONS_FILE"
echo "" >> "$SUGGESTIONS_FILE"
echo "根据项目分析，系统建议进行以下调整:" >> "$SUGGESTIONS_FILE"
echo "" >> "$SUGGESTIONS_FILE"

# 从调整文件中提取建议
python -c "
import json, sys
with open('$ADJUSTMENT_FILE', 'r', encoding='utf-8') as f:
    data = json.load(f)
adjustments = data.get('adjustments', [])
if not adjustments:
    print('没有建议的调整。', file=sys.stderr)
    print('- 没有建议的调整')
else:
    for adj in adjustments:
        milestone = adj.get('milestone', '未知里程碑')
        days = adj.get('adjustment_days', 0)
        direction = '延期' if days > 0 else '提前'
        old_date = adj.get('original_due_date', '未知')
        new_date = adj.get('new_due_date', '未知')
        print(f'- {milestone}: {direction} {abs(days)} 天 ({old_date} → {new_date})')
" >> "$SUGGESTIONS_FILE"

echo "" >> "$SUGGESTIONS_FILE"
echo "## 从分析报告中提取的建议" >> "$SUGGESTIONS_FILE"
echo "" >> "$SUGGESTIONS_FILE"

# 从分析报告中提取建议部分
python -c "
with open('$REPORT_FILE', 'r', encoding='utf-8') as f:
    report = f.read()
# 提取建议部分
import re
suggestions_section = re.search(r'## 建议操作\n\n(.*?)(?:\n\n##|\Z)', report, re.DOTALL)
if suggestions_section:
    print(suggestions_section.group(1))
else:
    print('无法从报告中提取建议。')
" >> "$SUGGESTIONS_FILE"

echo -e "\n5. 完成"
echo "项目周报自动分析和调整完成!"
echo "- 分析结果: $ANALYSIS_FILE"
echo "- 分析报告: $REPORT_FILE"
echo "- 调整建议: $SUGGESTIONS_FILE"
echo "- 调整结果: $ADJUSTMENT_FILE"

echo -e "\n请查看报告和调整建议，并决定是否应用调整。"
echo "若要应用调整，请运行以下命令:"
echo "python scripts/github/adjust_timeline.py --based-on-analysis \"$ANALYSIS_FILE\" --output \"$ADJUSTMENT_FILE\" --update-milestones \"true\""
