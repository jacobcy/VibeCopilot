"""
GitHub Data Mapper Module

Provides functions to map between local roadmap entities and GitHub entities.
"""
from typing import Any, Dict, Optional

# Placeholder - Actual local models (Roadmap, Milestone, Epic, Task) might be needed
# from src.models.db.roadmap import Roadmap, Milestone, Epic
# from src.models.db.task import Task


def map_roadmap_to_github_project(roadmap: Dict[str, Any]) -> Dict[str, Any]:
    """Maps local roadmap data to GitHub project creation payload."""
    roadmap_name = roadmap.get("name", "Unnamed Roadmap")
    return {
        "name": roadmap_name,
        "body": roadmap.get("description", f"{roadmap_name} - Project Tracking"),
    }


def map_milestone_to_github_milestone(milestone: Dict[str, Any]) -> Dict[str, Any]:
    """Maps local milestone data to GitHub milestone creation/update payload."""
    payload = {
        "title": milestone.get("name", f"Milestone {milestone.get('id', '')}"),
        "description": milestone.get("description", ""),
        # Map status (e.g., 'open', 'closed')
        "state": "open" if milestone.get("status", "open") == "open" else "closed",
    }
    # Add due_on if present and valid format for GitHub API
    # due_date = milestone.get("due_date")
    # if due_date:
    #     payload["due_on"] = ... # Format due_date correctly (e.g., ISO 8601)
    return payload


def map_epic_or_story_to_github_issue(
    item: Dict[str, Any], repo_owner: str, repo_name: str, github_milestone_id: Optional[int] = None
) -> Dict[str, Any]:
    """Maps a local Epic or Story to a GitHub issue creation/update payload."""

    # Determine issue title and body
    title_prefix = "[Epic]" if item.get("type") == "epic" else "[Story]"  # Assuming a 'type' field
    title = f"{title_prefix} {item.get('name', 'Unnamed Item')}"
    body = item.get("description", "")
    # Potentially add link back to local item in body
    # body += f"\n\nRef: local-{item.get('type')}-{item.get('id')}"

    payload = {
        "title": title,
        "body": body,
        "owner": repo_owner,
        "repo": repo_name,
        # Map status to GitHub issue state ('open' or 'closed')
        "state": "open" if item.get("status", "open") not in ["closed", "done", "completed"] else "closed",
        "labels": item.get("tags", []) + [item.get("type", "item")],  # Add type as label
    }

    if github_milestone_id:
        payload["milestone"] = github_milestone_id

    # Map assignee if available and corresponds to a GitHub user
    # assignee = item.get("assignee")
    # if assignee:
    #    payload["assignees"] = [assignee] # Assuming assignee is GitHub username

    return payload


def map_github_issue_to_task_update(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Maps relevant fields from a GitHub issue to update a local Task."""
    update_data = {
        "status": "closed" if issue.get("state") == "closed" else "open",  # Simple status mapping
        # Potentially update title, description, assignee if needed
        "assignee": issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
    }
    # Remove None values
    return {k: v for k, v in update_data.items() if v is not None}


def map_github_milestone_to_milestone_update(gh_milestone: Dict[str, Any]) -> Dict[str, Any]:
    """Maps relevant fields from a GitHub milestone to update a local Milestone."""
    update_data = {
        "status": gh_milestone.get("state", "open"),  # 'open' or 'closed'
        # Potentially update description, due_date
        "description": gh_milestone.get("description"),
        "due_date": gh_milestone.get("due_on"),  # May need date parsing
    }
    # Remove None values
    return {k: v for k, v in update_data.items() if v is not None}
