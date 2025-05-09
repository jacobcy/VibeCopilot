import os
import unittest
from unittest.mock import MagicMock, patch

from src.status.models import StatusSource

# Adjust import path as needed
from src.status.providers.github_info_provider import GitHubInfoProvider


class TestGitHubInfoProvider(unittest.TestCase):
    def setUp(self):
        self.provider = GitHubInfoProvider()

    @patch("src.status.providers.github_info_provider.os.environ.get")
    @patch("src.status.service.StatusService.get_instance")  # Patch get_instance where it's called from
    @patch("src.status.providers.github_info_provider.get_git_remote_info")
    @patch.object(GitHubInfoProvider, "is_gh_authenticated")  # Patch the static method
    def run_test_scenario(
        self,
        mock_is_gh_auth,
        mock_get_git_remote,
        mock_get_status_service_instance,
        mock_env_get,
        env_vars,
        settings_data,
        git_remote_data,
        gh_auth_status,
        expected_result,
    ):
        """Helper function to run a test scenario with mocked dependencies."""

        # Configure mocks
        mock_env_get.side_effect = lambda key, default=None: env_vars.get(key, default)

        # Mock for project_state.get_setting("github_info")
        mock_project_state = MagicMock()
        # Simulate get_setting correctly
        mock_project_state.get_setting = MagicMock(return_value=settings_data.get("github_info"))

        mock_status_service_instance = MagicMock()
        mock_status_service_instance.project_state = mock_project_state
        # Configure the mock for get_instance() to return our mock instance
        mock_get_status_service_instance.return_value = mock_status_service_instance

        mock_get_git_remote.return_value = git_remote_data
        mock_is_gh_auth.return_value = gh_auth_status

        # Execute
        status = self.provider.get_status()

        # Assert - check only the keys present in expected_result for flexibility
        for key, value in expected_result.items():
            self.assertEqual(status.get(key), value, f"Mismatch for key '{key}': expected {value}, got {status.get(key)}")

        # Optionally, assert that certain keys are NOT present if that's part of the contract
        self.assertNotIn("project_id", status, "project_id should not be in GitHubInfoProvider status")
        self.assertNotIn("project_title", status, "project_title should not be in GitHubInfoProvider status")
        self.assertNotIn("roadmap_title", status, "roadmap_title should not be in GitHubInfoProvider status")
        self.assertNotIn("effective_project_id", status, "effective_project_id should not be in GitHubInfoProvider status")

    def test_scenario_settings_configured_auth_ok(self):
        env_vars = {}
        settings_data = {"github_info": {"owner": "settings_owner", "repo": "settings_repo"}}
        git_remote_data = (None, None)
        gh_auth_status = True
        expected = {
            "effective_owner": "settings_owner",
            "effective_repo": "settings_repo",
            "source": StatusSource.SETTINGS_JSON.value,
            "configured": True,
            "is_cli_authenticated": True,
            "settings_owner": "settings_owner",
            "settings_repo": "settings_repo",
        }
        self.run_test_scenario(
            env_vars=env_vars, settings_data=settings_data, git_remote_data=git_remote_data, gh_auth_status=gh_auth_status, expected_result=expected
        )

    def test_scenario_env_configured_settings_missing_auth_ok(self):
        env_vars = {"GITHUB_OWNER": "env_owner", "GITHUB_REPO": "env_repo"}
        settings_data = {"github_info": None}  # or {} or missing github_info key
        git_remote_data = (None, None)
        gh_auth_status = True
        expected = {
            "effective_owner": "env_owner",
            "effective_repo": "env_repo",
            "source": StatusSource.ENV_VARIABLE.value,
            "configured": True,
            "is_cli_authenticated": True,
            "env_owner": "env_owner",
            "env_repo": "env_repo",
        }
        self.run_test_scenario(
            env_vars=env_vars, settings_data=settings_data, git_remote_data=git_remote_data, gh_auth_status=gh_auth_status, expected_result=expected
        )

    def test_scenario_git_detected_no_config_auth_fail(self):
        env_vars = {}
        settings_data = {}  # No settings.json config or github_info is empty/None
        # mock_get_git_remote.return_value in run_test_scenario expects a tuple (owner, repo)
        # but GitHubInfoProvider uses get_git_remote_info() which returns owner, repo directly.
        # Let's align run_test_scenario mock for get_git_remote to return a dict matching what GitHubInfoProvider might expect if it were more complex
        # or ensure get_git_remote_info in the main code is simple.
        # For now, assume get_git_remote_info returns (owner, repo) as used in provider.
        git_remote_data = ("git_owner", "git_repo")  # This matches what get_git_remote_info currently returns (a tuple)
        gh_auth_status = False
        expected_result = {
            "effective_owner": None,  # Since not configured via settings or env
            "effective_repo": None,
            "source": StatusSource.FALLBACK.value,  # Should be fallback if only detected by git
            "configured": False,
            "is_cli_authenticated": False,
            "detected_owner": "git_owner",  # This is where git detected info goes
            "detected_repo": "git_repo",
            "env_owner": None,  # Explicitly check these are None
            "settings_owner": None,
            "status_message": "GitHub仓库通过Git检测为 git_owner/git_repo，但未在VibeCopilot中正式配置。请运行 'vc status init' 进行确认和配置。 GitHub CLI 未认证。请运行 'gh auth login' 并确保 GITHUB_TOKEN 环境变量已设置。",
        }
        self.run_test_scenario(
            env_vars=env_vars,
            settings_data=settings_data,
            git_remote_data=git_remote_data,
            gh_auth_status=gh_auth_status,
            expected_result=expected_result,
        )

    def test_scenario_no_config_at_all_auth_fail(self):
        env_vars = {}
        settings_data = {}
        git_remote_data = (None, None)
        gh_auth_status = False
        expected = {
            "effective_owner": None,
            "effective_repo": None,
            "source": StatusSource.FALLBACK.value,
            "configured": False,
            "is_cli_authenticated": False,
            "status_message": "GitHub仓库未配置。请运行 'vc status init' 或设置 GITHUB_OWNER/GITHUB_REPO 环境变量。 GitHub CLI 未认证。请运行 'gh auth login' 并确保 GITHUB_TOKEN 环境变量已设置。",
        }
        self.run_test_scenario(
            env_vars=env_vars, settings_data=settings_data, git_remote_data=git_remote_data, gh_auth_status=gh_auth_status, expected_result=expected
        )

    def test_scenario_settings_configured_auth_fail(self):
        env_vars = {}
        settings_data = {"github_info": {"owner": "settings_owner", "repo": "settings_repo"}}
        git_remote_data = (None, None)
        gh_auth_status = False
        expected = {
            "effective_owner": "settings_owner",
            "effective_repo": "settings_repo",
            "source": StatusSource.SETTINGS_JSON.value,
            "configured": True,
            "is_cli_authenticated": False,
            "status_message": "GitHub CLI 未认证。请运行 'gh auth login' 并确保 GITHUB_TOKEN 环境变量已设置。",
        }
        self.run_test_scenario(
            env_vars=env_vars, settings_data=settings_data, git_remote_data=git_remote_data, gh_auth_status=gh_auth_status, expected_result=expected
        )

    # Can add more scenarios, e.g., only owner in settings, only repo, etc.
    # Test for is_gh_authenticated directly if needed, though it's static and might be tested elsewhere
    # or implicitly via these scenarios.


if __name__ == "__main__":
    unittest.main()
