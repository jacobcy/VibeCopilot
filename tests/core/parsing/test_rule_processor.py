"""
Tests for the RuleProcessor class.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.parsing.processors.rule_processor import RuleProcessor


class TestRuleProcessor:
    """Test cases for the RuleProcessor class."""

    @patch("src.parsing.parser_factory.create_parser")
    def test_process_rule(self, mock_create_parser):
        """Test processing rule content."""
        # Mock the parser
        mock_parser = MagicMock()
        mock_parser.parse_text.return_value = {
            "name": "Test Rule",
            "description": "This is a test rule",
            "type": "test",
            "sections": {"Description": "This is a test rule", "Examples": "Example content"},
        }
        mock_create_parser.return_value = mock_parser

        # Create processor and process rule
        processor = RuleProcessor(backend="regex")
        rule_content = "# Test Rule\n\nThis is a test rule."
        result = processor.process_rule(rule_content)

        # Verify parser was called correctly
        mock_parser.parse_text.assert_called_once_with(rule_content, "rule")

        # Verify result
        assert result["name"] == "Test Rule"
        assert result["description"] == "This is a test rule"
        assert result["type"] == "test"
        assert "sections" in result
        assert result["is_valid"] == True

    @patch("src.parsing.parser_factory.create_parser")
    def test_process_rule_file(self, mock_create_parser):
        """Test processing a rule file."""
        # Mock the parser
        mock_parser = MagicMock()
        mock_parser.parse_file.return_value = {
            "name": "Test Rule",
            "description": "This is a test rule",
            "type": "test",
            "sections": {"Description": "This is a test rule", "Examples": "Example content"},
        }
        mock_create_parser.return_value = mock_parser

        # Create processor
        processor = RuleProcessor(backend="regex")

        # Create a test file
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".mdc", delete=False) as f:
            f.write("# Test Rule\n\nThis is a test rule.")
            f.flush()
            file_path = f.name

        try:
            # Process the file
            result = processor.process_rule_file(file_path)

            # Verify parser was called correctly
            mock_parser.parse_file.assert_called_once_with(file_path, "rule")

            # Verify result
            assert result["name"] == "Test Rule"
            assert result["description"] == "This is a test rule"
            assert result["type"] == "test"
            assert "sections" in result
            assert result["is_valid"] == True
            assert "file_path" in result
            assert "file_name" in result
            assert "rule_id" in result
        finally:
            os.unlink(file_path)

    @patch("src.parsing.parser_factory.create_parser")
    def test_process_rule_directory(self, mock_create_parser):
        """Test processing a directory of rule files."""
        # Mock the parser
        mock_parser = MagicMock()
        mock_parser.parse_directory.return_value = [
            {
                "name": "Rule 1",
                "description": "Description 1",
                "type": "test",
                "file_path": "/path/to/rule1.mdc",
            },
            {
                "name": "Rule 2",
                "description": "Description 2",
                "type": "test",
                "file_path": "/path/to/rule2.mdc",
            },
        ]
        mock_create_parser.return_value = mock_parser

        # Create processor
        processor = RuleProcessor(backend="regex")

        # Process the directory
        results = processor.process_rule_directory("/path/to/rules")

        # Verify parser was called correctly
        mock_parser.parse_directory.assert_called_once_with("/path/to/rules", "*.mdc", "rule", True)

        # Verify results
        assert len(results) == 2
        assert results[0]["name"] == "Rule 1"
        assert results[1]["name"] == "Rule 2"
        assert results[0]["is_valid"] == True
        assert results[1]["is_valid"] == True

    @patch("src.parsing.parser_factory.create_parser")
    def test_validate_and_enhance(self, mock_create_parser):
        """Test validation and enhancement of parsed rule data."""
        # Create processor
        mock_create_parser.return_value = MagicMock()
        processor = RuleProcessor(backend="regex")

        # Test with complete data
        complete_data = {"name": "Test Rule", "description": "This is a test rule", "type": "test"}
        result = processor._validate_and_enhance(complete_data)
        assert result["is_valid"] == True
        assert "missing_fields" not in result

        # Test with missing fields
        incomplete_data = {"name": "Test Rule"}
        result = processor._validate_and_enhance(incomplete_data)
        assert result["is_valid"] == False
        assert "missing_fields" in result
        assert "description" in result["missing_fields"]

        # Test inferring missing fields
        inferred_data = {
            "title": "Test Rule",
            "sections": {"Introduction": "This could be inferred as a description."},
        }
        result = processor._validate_and_enhance(inferred_data)
        assert "name" in result
        assert result["name"] == "Test Rule"  # Inferred from title
        assert "description" in result
        assert result["is_valid"] == True
