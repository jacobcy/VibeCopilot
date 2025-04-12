"""
GitHub API Facade Module

Provides a simplified interface for interacting with GitHub Projects and Issues APIs
relevant to roadmap synchronization.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

# 直接从实际模块导入
from adapters.github_project.api.clients.issues_client import GitHubIssuesClient
from adapters.github_project.api.clients.projects_client import GitHubProjectsClient

logger = logging.getLogger(__name__)


class GitHubApiFacade:
    """Facade for GitHub Projects and Issues API interactions."""

    def __init__(self, token: str, owner: str, repo: str):
        if not all([token, owner, repo]):
            raise ValueError("GitHub token, owner, and repo must be provided.")

        self.token = token
        self.owner = owner
        self.repo = repo
        self.projects_client = GitHubProjectsClient(token=self.token)
        self.issues_client = GitHubIssuesClient(token=self.token)

        # Simple in-memory cache for frequently accessed items during a sync operation
        self._project_cache: Dict[str, Dict] = {}  # Cache by roadmap name -> project data
        self._milestone_cache: Dict[str, Dict] = {}  # Cache by local milestone ID -> gh milestone data
        self._issue_cache: Dict[str, Dict] = {}  # Cache by local item ID -> gh issue data

    def clear_cache(self):
        """Clears the internal cache."""
        self._project_cache = {}
        self._milestone_cache = {}
        self._issue_cache = {}

    def get_or_create_project(self, name: str, body: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Gets a GitHub project by name, or creates it if not found.

        Args:
            name: Project name/title
            body: Project description

        Returns:
            Optional[Dict[str, Any]]: Project data if found or created, None if failed
        """
        if name in self._project_cache:
            return self._project_cache[name]

        try:
            projects = self.projects_client.get_projects(self.owner, self.repo)
            for project in projects:
                if project.get("title") == name:
                    self._project_cache[name] = project
                    logger.info(f"Found existing GitHub project: '{name}' (ID: {project.get('id')})")
                    return project

            # Not found, create it
            logger.info(f"GitHub project '{name}' not found. Creating...")
            new_project = self.projects_client.create_project(
                self.owner, self.repo, name, body or f"{name} - Project Tracking"  # This is the title  # This is the description
            )
            if new_project:
                self._project_cache[name] = new_project
            return new_project
        except Exception as e:
            logger.error(f"Error getting or creating GitHub project '{name}': {e}", exc_info=True)
            return None

    def get_or_create_milestone(
        self,
        title: str,
        local_id: str,
        description: Optional[str] = None,
        state: str = "open",
        due_on: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Gets a GitHub milestone by title, or creates it if not found."""
        if local_id in self._milestone_cache:
            return self._milestone_cache[local_id]

        try:
            milestones = self.issues_client.get_milestones(self.owner, self.repo)
            for gh_milestone in milestones:
                if gh_milestone.get("title") == title:
                    self._milestone_cache[local_id] = gh_milestone
                    logger.info(f"Found existing GitHub milestone: '{title}' (ID: {gh_milestone.get('id')})")
                    return gh_milestone

            # Not found, create it
            logger.info(f"GitHub milestone '{title}' not found. Creating...")
            milestone_data = {
                "title": title,
                "state": state,
                "description": description or "",
            }
            if due_on:  # Add due_on only if provided (ensure correct format)
                milestone_data["due_on"] = due_on

            new_milestone = self.issues_client.create_milestone(self.owner, self.repo, milestone_data)
            self._milestone_cache[local_id] = new_milestone
            return new_milestone
        except Exception as e:
            logger.error(f"Error getting or creating GitHub milestone '{title}': {e}", exc_info=True)
            return None

    def find_issue_by_title(self, title_part: str) -> Optional[Dict[str, Any]]:
        """Finds the first open GitHub issue containing a specific title part."""
        # Note: This can be inefficient. Consider adding labels or identifiers for better lookup.
        try:
            # Search for open issues containing the title part
            # The search might need to be more specific depending on the adapter
            issues = self.issues_client.search_issues(self.owner, self.repo, query=f'state:open in:title "{title_part}"')

            if issues:  # Assuming search returns a list
                # TODO: Add better matching logic if needed (e.g., exact title prefix)
                logger.info(f"Found potential matching issue for '{title_part}': ID {issues[0].get('id')}")
                return issues[0]
            return None
        except Exception as e:
            logger.error(
                f"Error searching for GitHub issue with title part '{title_part}': {e}",
                exc_info=True,
            )
            return None

    def create_issue(self, issue_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Creates a new GitHub issue."""
        try:
            # The payload should already be prepared by the mapper
            new_issue = self.issues_client.create_issue(self.owner, self.repo, issue_data)
            logger.info(f"Created GitHub issue '{issue_data.get('title')}' (ID: {new_issue.get('id')})")
            return new_issue
        except Exception as e:
            logger.error(f"Error creating GitHub issue '{issue_data.get('title')}': {e}", exc_info=True)
            return None

    def update_issue(self, issue_number: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates an existing GitHub issue."""
        try:
            # The payload should already be prepared by the mapper
            updated_issue = self.issues_client.update_issue(self.owner, self.repo, issue_number, update_data)
            logger.info(f"Updated GitHub issue #{issue_number}")
            return updated_issue
        except Exception as e:
            logger.error(f"Error updating GitHub issue #{issue_number}: {e}", exc_info=True)
            return None

    def get_issue(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """Gets details for a specific GitHub issue."""
        try:
            issue = self.issues_client.get_issue(self.owner, self.repo, issue_number)
            return issue
        except Exception as e:
            logger.error(f"Error getting GitHub issue #{issue_number}: {e}", exc_info=True)
            return None

    def get_issues_by_milestone(self, milestone_number: int, state: str = "all") -> List[Dict[str, Any]]:
        """Gets all issues associated with a specific milestone."""
        try:
            # Assuming the client has a method like this, adjust if needed
            issues = self.issues_client.get_issues_for_milestone(self.owner, self.repo, milestone_number, state=state)
            return issues
        except Exception as e:
            logger.error(f"Error getting issues for GitHub milestone #{milestone_number}: {e}", exc_info=True)
            return []

    # Add methods for adding issues to projects if needed
    # def add_issue_to_project(self, project_id: int, issue_node_id: str) -> bool:
    #     ...

    # Add methods for getting project columns/fields if needed for status mapping
    # def get_project_columns(self, project_id: int) -> List[Dict]:
    #     ...
