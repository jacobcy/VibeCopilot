import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

# Assuming ProjectState is in src.status.core.project_state
# Adjust the import path based on your project structure and how pytest/unittest discovers modules
# For example, if your tests directory is at the same level as src:
from src.status.core.project_state import ProjectState


class TestProjectState(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to store state and settings files for tests
        self.test_dir = tempfile.mkdtemp()
        self.state_file_path = os.path.join(self.test_dir, "project_state.json")
        self.settings_file_path = os.path.join(self.test_dir, ".vibecopilot", "config", "settings.json")

        # Ensure the directory for settings.json exists
        os.makedirs(os.path.dirname(self.settings_file_path), exist_ok=True)

        # Mock for PROJECT_ROOT or other path dependencies if ProjectState uses them directly
        # For _get_state_file_path, we might need to patch it if it's not easily configurable
        # or ensure ProjectState can be initialized with a direct path for testing.

    def tearDown(self):
        # Remove the temporary directory and its contents after tests
        shutil.rmtree(self.test_dir)

    def _write_json_file(self, file_path, data):
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def test_initialization_new_file(self):
        """Test ProjectState initialization when state file does not exist and .env is ignored."""
        original_os_path_exists = os.path.exists

        def mock_os_exists_side_effect(path_arg):
            if path_arg == self.state_file_path:
                return False
            if path_arg == os.path.dirname(self.state_file_path):
                return True
            if path_arg == ".env":  # This is checked by _load_from_env
                return False  # Simulate .env not existing for this test
            return original_os_path_exists(path_arg)

        with patch(
            "src.status.core.project_state.os.path.exists", side_effect=mock_os_exists_side_effect
        ) as mock_path_exists_in_module, patch.object(ProjectState, "_get_state_file_path", return_value=self.state_file_path):
            # Removed mock of _load_from_env method itself

            self.assertFalse(original_os_path_exists(self.state_file_path))

            ps = ProjectState(state_file=self.state_file_path)

            # _load_from_env IS called if state file doesn't exist.
            # We assert that the check for .env inside _load_from_env happened and was mocked.
            mock_path_exists_in_module.assert_any_call(self.state_file_path)
            mock_path_exists_in_module.assert_any_call(".env")

            self.assertEqual(ps._state, {})
            self.assertFalse(original_os_path_exists(self.state_file_path))

            ps.set_project_name("FirstSave")

            self.assertTrue(original_os_path_exists(self.state_file_path))
            with open(self.state_file_path, "r") as f:
                saved_data = json.load(f)
            self.assertIn("last_updated", saved_data)
            self.assertEqual(saved_data.get("name"), "FirstSave")
            self.assertNotIn("current_phase", saved_data)  # Because .env was mocked to not exist

    def test_initialization_existing_file(self):
        """Test ProjectState initialization when the state file exists."""
        initial_data = {"name": "TestProject", "current_phase": "dev", "last_updated": "sometime"}
        self._write_json_file(self.state_file_path, initial_data)

        with patch.object(ProjectState, "_get_state_file_path", return_value=self.state_file_path):
            # We don't need to mock os.path.exists here if the file actually exists for _load_state
            ps = ProjectState(state_file=self.state_file_path)
            self.assertEqual(ps._state.get("name"), "TestProject")
            self.assertEqual(ps._state.get("current_phase"), "dev")

    @patch("src.status.core.project_state.file_utils.read_json_file")
    @patch("src.status.core.project_state.os.path.exists")
    def test_set_and_get_project_name(self, mock_exists_in_module, mock_read_json):
        """Test setting and getting the project name, including fallback."""

        original_os_path_exists = os.path.exists  # Keep a reference to the real os.path.exists

        with patch.object(ProjectState, "_get_state_file_path", return_value=self.state_file_path):
            ps = ProjectState(state_file=self.state_file_path)

            # --- Scenario 1: Set name in state, should be retrieved ---
            def exists_side_effect_s1(path_arg):
                if path_arg == ".vibecopilot/config/settings.json":
                    return False
                # Use the original os.path.exists for other paths to avoid recursion
                return original_os_path_exists(path_arg)

            mock_exists_in_module.side_effect = exists_side_effect_s1

            save_success = ps.set_project_name("MyStateProject")
            self.assertTrue(save_success, "set_project_name should return True on successful save")

            self.assertEqual(ps.get_project_name(), "MyStateProject", "Should retrieve name set in state")
            self.assertTrue(original_os_path_exists(self.state_file_path), f"State file {self.state_file_path} should exist after saving.")
            with open(self.state_file_path, "r") as f:
                saved_data = json.load(f)
            self.assertEqual(saved_data.get("name"), "MyStateProject", "Name should be saved to file")

            # --- Scenario 2: State name is "未设置", fallback to settings ---
            def exists_side_effect_s2(path_arg):
                if path_arg == ".vibecopilot/config/settings.json":
                    return True
                # For calls to os.path.exists for the state file itself, or its directory,
                # assume they might be checked by _save_state or other internal logic.
                # If state file is checked by _load_state (it is if name is bad), let it be false.
                if path_arg == self.state_file_path:
                    return False  # Simulating it doesn't exist for a potential reload by get_project_name
                if path_arg == os.path.dirname(self.state_file_path):
                    return True  # Parent dir exists
                return original_os_path_exists(path_arg)

            mock_exists_in_module.side_effect = exists_side_effect_s2
            mock_read_json.return_value = {"project": {"name": "SettingsProjectName"}}

            ps.set_project_name("未设置")
            self.assertEqual(ps.get_project_name(), "SettingsProjectName", "Should fallback to settings name when state is '未设置'")
            mock_read_json.assert_called_with(".vibecopilot/config/settings.json")

            # --- Scenario 3: State name is None, fallback to settings ---
            ps._state["name"] = None
            # Re-use exists_side_effect_s2 or create a similar one if needed
            mock_exists_in_module.side_effect = exists_side_effect_s2
            mock_read_json.return_value = {"project": {"name": "SettingsProjectName"}}
            self.assertEqual(ps.get_project_name(), "SettingsProjectName", "Should fallback to settings name when state is None")
            mock_read_json.assert_called_with(".vibecopilot/config/settings.json")

            # --- Scenario 4: State name is "未设置", settings file doesn't exist ---
            ps.set_project_name("未设置")

            def exists_side_effect_s4(path_arg):
                if path_arg == ".vibecopilot/config/settings.json":
                    return False
                if path_arg == self.state_file_path:  # For _load_state if triggered
                    return True  # Assume state file itself exists (as it was just saved)
                if path_arg == os.path.dirname(self.state_file_path):
                    return True
                return original_os_path_exists(path_arg)

            mock_exists_in_module.side_effect = exists_side_effect_s4
            self.assertEqual(ps.get_project_name(), "未设置", "Should return '未设置' when state is '未设置' and settings fallback fails (no file)")

            # --- Scenario 5: State name is None, settings file doesn't exist ---
            ps._state["name"] = None
            mock_exists_in_module.side_effect = exists_side_effect_s4  # Can reuse s4 logic
            self.assertEqual(ps.get_project_name(), "未设置", "Should return default '未设置' when state is None and settings fallback fails (no file)")

            # --- Scenario 6: State name is "未设置", settings exists but has no name ---
            ps.set_project_name("未设置")

            def exists_side_effect_s6(path_arg):
                if path_arg == ".vibecopilot/config/settings.json":
                    return True
                if path_arg == self.state_file_path:
                    return True
                if path_arg == os.path.dirname(self.state_file_path):
                    return True
                return original_os_path_exists(path_arg)

            mock_exists_in_module.side_effect = exists_side_effect_s6
            mock_read_json.return_value = {"project": {}}
            self.assertEqual(ps.get_project_name(), "未设置", "Should return '未设置' when state is '未设置' and settings has no name")

    def test_set_current_roadmap_id(self):
        """Test set_current_roadmap_id and its effect on active_roadmap_backend_config."""
        with patch.object(ProjectState, "_get_state_file_path", return_value=self.state_file_path):
            ps = ProjectState(state_file=self.state_file_path)
            ps._state["active_roadmap_backend_config"] = {"github": {"owner": "test"}}  # Pre-populate

            ps.set_current_roadmap_id("rm_123")
            self.assertEqual(ps.get_current_roadmap_id(), "rm_123")
            self.assertEqual(ps._state.get("active_roadmap_backend_config"), {})

            ps._state["active_roadmap_backend_config"] = {"github": {"owner": "test2"}}
            ps.set_current_roadmap_id("rm_123")  # Set same ID
            self.assertNotEqual(ps._state.get("active_roadmap_backend_config"), {})
            self.assertEqual(ps._state.get("active_roadmap_backend_config").get("github").get("owner"), "test2")

    def test_active_roadmap_backend_config_methods(self):
        """Test set, get, and clear methods for active_roadmap_backend_config."""
        with patch.object(ProjectState, "_get_state_file_path", return_value=self.state_file_path):
            ps = ProjectState(state_file=self.state_file_path)

            github_config = {"owner": "testowner", "repo": "testrepo", "project_id": "pid_123"}
            ps.set_active_roadmap_backend_config("github", github_config)

            retrieved_config = ps.get_active_roadmap_backend_config("github")
            self.assertEqual(retrieved_config, github_config)

            full_backend_config = ps.get_active_roadmap_backend_config()
            self.assertEqual(full_backend_config.get("backend_type"), "github")
            self.assertEqual(full_backend_config.get("github"), github_config)

            ps.clear_active_roadmap_backend_config("github")
            self.assertIsNone(ps.get_active_roadmap_backend_config("github"))
            full_backend_config_after_clear = ps.get_active_roadmap_backend_config()
            self.assertEqual(full_backend_config_after_clear.get("backend_type"), "")

    def test_roadmap_github_mapping_methods(self):
        """Test set_roadmap_github_project and get_github_project_id_for_roadmap."""
        with patch.object(ProjectState, "_get_state_file_path", return_value=self.state_file_path):
            ps = ProjectState(state_file=self.state_file_path)

            ps.set_roadmap_github_project("local_rm_1", "gh_proj_node_A")
            ps.set_roadmap_github_project("local_rm_2", "gh_proj_node_B")

            self.assertEqual(ps.get_github_project_id_for_roadmap("local_rm_1"), "gh_proj_node_A")
            self.assertEqual(ps.get_github_project_id_for_roadmap("local_rm_2"), "gh_proj_node_B")
            self.assertIsNone(ps.get_github_project_id_for_roadmap("local_rm_3"))

            ps.set_roadmap_github_project("local_rm_1", "gh_proj_node_C")  # Overwrite
            self.assertEqual(ps.get_github_project_id_for_roadmap("local_rm_1"), "gh_proj_node_C")

            with open(self.state_file_path, "r") as f:
                saved_data = json.load(f)
            self.assertEqual(saved_data.get("roadmap_github_mapping").get("local_rm_1"), "gh_proj_node_C")

            ps._state["current_roadmap_id"] = "local_rm_1"  # Make it active
            ps._state["active_roadmap_backend_config"] = {}  # Clear it

            ps.set_roadmap_github_project("local_rm_1", "gh_proj_node_D")  # Set mapping again
            self.assertEqual(
                ps._state.get("active_roadmap_backend_config"), {}, "set_roadmap_github_project should not update active_roadmap_backend_config"
            )


if __name__ == "__main__":
    unittest.main()
