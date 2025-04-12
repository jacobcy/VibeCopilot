#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name="vibe-copilot",
    version="0.1.0",
    description="VibeCopilot - AI辅助开发工具",
    author="Jacob Chen",
    packages=find_packages(exclude=["tests", "docs"]),
    python_requires=">=3.8.0",
    install_requires=[
        "python-dotenv>=0.19.0",
        "requests>=2.25.0",
        "sqlalchemy>=1.4.0",
        "pyyaml>=6.0",
        "python-frontmatter>=1.0.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
