"""
Git 相关工具函数
"""

import logging
import re
from typing import Optional, Tuple

try:
    import git
    from git.exc import InvalidGitRepositoryError, NoSuchPathError
except ImportError:
    git = None  # type: ignore
    InvalidGitRepositoryError = Exception  # type: ignore # Use base Exception if git not installed
    NoSuchPathError = Exception  # type: ignore # Use base Exception

logger = logging.getLogger(__name__)


def get_git_remote_info(repo_path: str = ".") -> Tuple[Optional[str], Optional[str]]:
    """
    获取指定路径 Git 仓库 'origin' 远程的 owner 和 repo_name。

    Args:
        repo_path: 仓库的本地路径 (默认为当前目录)。

    Returns:
        一个包含 (owner, repo_name) 的元组，如果无法获取则返回 (None, None)。
    """
    if git is None:
        logger.error("GitPython 库未安装。请运行 'pip install GitPython'")
        return None, None

    try:
        # Use search_parent_directories=True to find .git folder upwards
        repo = git.Repo(repo_path, search_parent_directories=True)
        repo_dir = repo.working_dir  # Get the actual repo root
        logger.debug(f"找到Git仓库: {repo_dir}")
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        logger.warning(f"路径 '{repo_path}' 或其父目录不是一个有效的 Git 仓库: {e}")
        return None, None
    except Exception as e:
        logger.error(f"初始化 Git 仓库对象时出错: {e}")
        return None, None

    if not repo.remotes:
        logger.warning(f"仓库 '{repo_dir}' 没有配置远程仓库。")
        return None, None

    # 尝试获取origin远程仓库
    origin_remote = None
    try:
        origin_remote = repo.remotes.origin
        logger.debug(f"找到origin远程仓库: {origin_remote}")
    except AttributeError:
        logger.warning(f"仓库 '{repo_dir}' 找不到名为 'origin' 的远程仓库。")
        # 尝试使用第一个远程仓库
        if repo.remotes:
            origin_remote = repo.remotes[0]
            logger.info(f"使用第一个可用的远程仓库: '{origin_remote.name}'")
        else:
            return None, None

    if not origin_remote.urls:
        logger.warning(f"远程仓库 '{origin_remote.name}' 在 '{repo_dir}' 中没有配置 URL。")
        return None, None

    # 记录所有远程URL
    logger.debug(f"远程仓库URLs: {list(origin_remote.urls)}")

    # 支持更多的URL格式
    for remote_url in origin_remote.urls:
        logger.debug(f"处理远程URL: {remote_url}")

        # 尝试不同的正则表达式模式
        patterns = [
            # 标准GitHub HTTPS和SSH URL模式
            r"[:/]([^/]+?)/([^/]+?)(?:\.git)?$",
            # GitHub直接URL
            r"github\.com/([^/]+)/([^/]+)",
            # 子域名格式
            r"([^/]+?)\.github\.io/([^/]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, remote_url)
            if match:
                owner = match.group(1)
                repo_name = match.group(2)
                logger.info(f"从 URL '{remote_url}' 在仓库 '{repo_dir}' 检测到: {owner}/{repo_name}")
                return owner, repo_name

        # 如果上面的模式都不匹配，尝试手动解析
        if "github.com" in remote_url:
            parts = remote_url.split("github.com/")
            if len(parts) > 1:
                path_parts = parts[1].split("/")
                if len(path_parts) >= 2:
                    owner = path_parts[0]
                    repo_name = path_parts[1].replace(".git", "")
                    logger.info(f"手动从URL '{remote_url}' 解析: {owner}/{repo_name}")
                    return owner, repo_name

    # 如果所有尝试都失败，返回None
    logger.warning("无法从Git远程库解析GitHub信息，请运行 'vc status init' 命令配置GitHub信息")
    return None, None


# Example usage (for testing)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"测试当前目录...")
    owner, repo = get_git_remote_info()
    if owner and repo:
        print(f"检测到仓库: {owner}/{repo}")
    else:
        print("无法检测到仓库信息。")

    # print("\n测试指定路径...")
    # # Test with a specific path (replace with a valid path on your system)
    # # test_path = '/path/to/your/repo'
    # # owner_s, repo_s = get_git_remote_info(test_path)
    # # if owner_s and repo_s:
    # #     print(f"Detected Repository (specific path: {test_path}): {owner_s}/{repo_s}")
    # # else:
    # #     print(f"Could not detect repository information for specific path: {test_path}")
