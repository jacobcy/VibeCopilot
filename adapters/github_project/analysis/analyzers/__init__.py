#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub项目分析器包.

提供多种项目分析功能。
"""

from .progress_analyzer import analyze_milestones_progress, analyze_progress, categorize_by_status
from .quality_analyzer import analyze_quality
from .report_generator import (
    extract_key_points,
    generate_markdown_report,
    generate_recommendations,
    generate_report,
)
from .risk_analyzer import analyze_risks, calculate_risk_level, check_delayed_items

__all__ = [
    "analyze_progress",
    "analyze_quality",
    "analyze_risks",
    "analyze_milestones_progress",
    "categorize_by_status",
    "calculate_risk_level",
    "check_delayed_items",
    "generate_report",
    "generate_markdown_report",
    "extract_key_points",
    "generate_recommendations",
]
