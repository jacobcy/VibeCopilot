#!/usr/bin/env python3
"""VibeCopilot安装配置脚本."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vibecopilot",
    version="0.1.0",
    author="VibeCopilot Contributors",
    author_email="example@example.com",
    description="AI辅助项目管理工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/vibecopilot",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8,<3.14",
    install_requires=[
        "pydantic>=2.5.0",
        "typer>=0.9.0",
        "rich>=13.4.0",
        "jinja2>=3.1.2",
        "pyyaml>=6.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "langchain>=0.0.334",
        "langchain-openai>=0.0.2",
        "langchain-community>=0.0.10",
        "openai>=1.0.0",
        "faiss-cpu>=1.7.4",
        "chromadb>=0.4.18",
        "sentence-transformers>=2.2.2",
        "unstructured>=0.10.30",
        "markdown>=3.4.4",
        "beautifulsoup4>=4.12.2",
        "python-frontmatter>=1.0.0",
        "sqlalchemy>=2.0.20",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.9.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
            "flake8>=6.1.0",
            "pre-commit>=3.4.0",
        ],
        "docs": [
            "mkdocs>=1.5.2",
            "mkdocs-material>=9.2.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "vibecopilot=src.cli.main:main",
        ],
    },
    include_package_data=True,
)
