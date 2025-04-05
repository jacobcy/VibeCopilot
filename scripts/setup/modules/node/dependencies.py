#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Node.js依赖管理模块，处理依赖安装和验证。
"""

from pathlib import Path

from ..common import IS_WINDOWS, PROJECT_ROOT, run_command


def install_node_dependencies() -> bool:
    """安装Node.js依赖包，包括markdownlint-cli."""
    print("正在安装Node.js依赖...")

    # 检查package.json是否存在
    package_json = PROJECT_ROOT / "package.json"
    if not package_json.exists():
        print("错误: 未找到package.json文件")
        return False

    # 尝试安装前输出一些诊断信息
    print("正在检查package.json内容...")
    try:
        import json

        with open(package_json, "r", encoding="utf-8") as f:
            pkg_data = json.load(f)

        # 输出依赖信息
        if "dependencies" in pkg_data:
            print(f"发现 {len(pkg_data['dependencies'])} 个依赖项")
            for pkg, version in pkg_data["dependencies"].items():
                if pkg.startswith("@uvx/"):
                    print(f"警告: 检测到可能的私有包 {pkg}@{version}")
                    print(f"      - @uvx 包通常需要通过uvx命令安装而非npm/pnpm")

        if "devDependencies" in pkg_data:
            print(f"发现 {len(pkg_data['devDependencies'])} 个开发依赖项")

    except json.JSONDecodeError:
        print("警告: package.json解析失败，可能格式不正确")
    except Exception as e:
        print(f"警告: 检查package.json时出错: {e}")

    # 执行安装
    print("\n开始安装依赖...")
    returncode, output = run_command(["pnpm", "install"], cwd=PROJECT_ROOT)
    if returncode != 0:
        print("\n❌ 安装Node.js依赖失败")
        print("-" * 60)
        print(output)
        print("-" * 60)

        # 提供可能的解决方案
        if "404" in output:
            print("\n可能的原因: 包不存在或无权访问")
            print("解决方案:")
            print("1. 检查package.json中的包名是否正确")
            print("2. 检查是否为私有包（如@uvx/*），这类包可能需要特殊处理")
            print("3. 确认网络连接是否正常")

        elif "EACCES" in output:
            print("\n可能的原因: 权限不足")
            print("解决方案: 尝试使用sudo运行或修复权限问题")

        elif "ECONNREFUSED" in output:
            print("\n可能的原因: 网络连接问题")
            print("解决方案: 检查网络连接，确认能够访问npm仓库")

        else:
            print("\n建议尝试以下步骤:")
            print("1. 运行 `pnpm install --no-frozen-lockfile` 重新生成lockfile")
            print("2. 检查package.json中是否包含私有包或不存在的包")
            print("3. 手动安装单个包来定位问题: `pnpm add <包名>`")

        return False

    # 验证markdownlint-cli已安装
    returncode, output = run_command(
        ["pnpm", "exec", "markdownlint", "--version"], cwd=PROJECT_ROOT
    )
    if returncode != 0:
        print("\n警告: markdownlint-cli安装验证失败，尝试单独安装...")
        returncode, output = run_command(
            ["pnpm", "add", "--save-dev", "markdownlint-cli"], cwd=PROJECT_ROOT
        )
        if returncode != 0:
            print(f"安装markdownlint-cli失败: {output}")
            return False

    print("\n✅ Node.js依赖安装完成")
    return True


def verify_markdownlint() -> bool:
    """验证markdownlint可执行性，创建符号链接确保pre-commit能找到它."""
    import os

    from ..common import update_shell_path

    print("验证markdownlint配置...")
    # 检查pnpm exec markdownlint是否可执行
    returncode, output = run_command(
        ["pnpm", "exec", "markdownlint", "--version"], cwd=PROJECT_ROOT
    )
    if returncode != 0:
        print(f"markdownlint验证失败: {output}")
        return False

    # 获取markdownlint路径
    node_bin = Path(PROJECT_ROOT) / "node_modules" / ".bin"
    markdownlint_path = node_bin / ("markdownlint.cmd" if IS_WINDOWS else "markdownlint")

    if not markdownlint_path.exists():
        print(f"未找到markdownlint可执行文件: {markdownlint_path}")
        return False

    # 检查PATH环境变量中是否包含node_modules/.bin
    path_env = os.environ.get("PATH", "")
    node_bin_str = str(node_bin)

    if node_bin_str not in path_env:
        print(f"将{node_bin}添加到环境变量PATH中...")
        update_shell_path(node_bin_str)

    # 打印使用说明
    print("markdownlint验证完成.")
    print('如需手动运行markdownlint，请使用: pnpm exec markdownlint --fix "**/*.md"')
    return True


def check_package_dependencies() -> None:
    """检查项目中的package.json依赖版本，识别潜在的冲突问题."""
    print("\n---- 依赖版本检查 ----")
    import glob
    import json
    from pathlib import Path

    # 查找所有package.json文件
    package_files = glob.glob(str(PROJECT_ROOT / "**/package.json"), recursive=True)

    # 排除node_modules中的package.json
    package_files = [f for f in package_files if "node_modules" not in f]

    if not package_files:
        print("未找到package.json文件")
        return

    print(f"找到 {len(package_files)} 个package.json文件")

    # 潜在问题列表
    potential_issues = []

    # 检查清单
    problematic_deps = {
        "react": {
            "warning": lambda v: v.startswith("^19") or v.startswith("19"),
            "message": "React 19仍处于预发布状态，可能导致依赖冲突，建议使用React 18.2.0",
        },
        "@docusaurus/core": {
            "warning": lambda v: v.startswith("^3") or v.startswith("3"),
            "recommended_react": "^18.2.0",
        },
    }

    # 遍历每个package.json
    for pkg_file in package_files:
        try:
            with open(pkg_file, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)

            pkg_path = Path(pkg_file).relative_to(PROJECT_ROOT)
            dependencies = pkg_data.get("dependencies", {})

            # 检查特定版本问题
            for dep, dep_info in problematic_deps.items():
                if dep in dependencies:
                    version = dependencies[dep]

                    # 检查是否为问题版本
                    if "warning" in dep_info and dep_info["warning"](version):
                        issue = {
                            "file": str(pkg_path),
                            "package": dep,
                            "version": version,
                            "message": dep_info.get("message", f"可能存在依赖冲突问题"),
                        }
                        potential_issues.append(issue)

                    # 检查相关依赖
                    if dep == "@docusaurus/core" and "react" in dependencies:
                        react_version = dependencies["react"]
                        recommended = dep_info.get("recommended_react")
                        if recommended and react_version != recommended:
                            issue = {
                                "file": str(pkg_path),
                                "package": "react",
                                "version": react_version,
                                "message": f"使用Docusaurus时，建议React版本为{recommended}",
                            }
                            potential_issues.append(issue)

        except Exception as e:
            print(f"解析 {pkg_file} 时出错: {e}")

    # 输出发现的问题
    if potential_issues:
        print("\n⚠️ 发现以下潜在依赖问题:")
        for issue in potential_issues:
            print(f"  - {issue['file']}: {issue['package']}@{issue['version']}")
            print(f"    {issue['message']}")
        print("\n建议修复这些问题以避免依赖冲突")
    else:
        print("✅ 未发现明显的依赖冲突问题")
