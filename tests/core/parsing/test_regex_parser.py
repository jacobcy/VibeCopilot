"""
Tests for the RegexParser class.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.core.parsing.parsers.regex_parser import RegexParser


class TestRegexParser:
    """Test cases for the RegexParser class."""

    def test_parse_text_rule(self):
        """Test parsing rule text."""
        parser = RegexParser()

        rule_text = """# Test Rule

## Description
This is a test rule.

## Parameters
- param1: Value1
- param2: Value2

## Examples
```
Example 1
```
"""

        result = parser.parse_text(rule_text, "rule")

        assert "title" in result
        assert result["title"] == "Test Rule"
        assert "sections" in result
        assert "Description" in result["sections"]
        assert "Parameters" in result["sections"]
        assert "Examples" in result["sections"]
        assert len(result["codeBlocks"]) == 1

    def test_parse_text_document(self):
        """Test parsing document text."""
        parser = RegexParser()

        doc_text = """# Test Document

## Introduction
This is a test document.

## Links
[Example Link](https://example.com)

## Code
```python
def hello_world():
    print("Hello, world!")
```
"""

        result = parser.parse_text(doc_text, "document")

        assert "title" in result
        assert result["title"] == "Test Document"
        assert "sections" in result
        assert "Introduction" in result["sections"]
        assert "Links" in result["sections"]
        assert "Code" in result["sections"]
        assert len(result["codeBlocks"]) == 1
        assert result["codeBlocks"][0]["language"] == "python"
        assert len(result["links"]) == 1
        assert result["links"][0]["url"] == "https://example.com"

    def test_parse_file(self):
        """Test parsing a file."""
        parser = RegexParser()

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as f:
            f.write(
                """# Test File

## Content
This is a test file.
"""
            )
            f.flush()
            file_path = f.name

        try:
            result = parser.parse_file(file_path)

            assert "title" in result
            assert result["title"] == "Test File"
            assert "sections" in result
            assert "Content" in result["sections"]
            assert "file_path" in result
            assert "file_name" in result
        finally:
            os.unlink(file_path)

    def test_parse_directory(self):
        """Test parsing a directory."""
        parser = RegexParser()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(3):
                file_path = Path(temp_dir) / f"test_{i}.md"
                with open(file_path, "w") as f:
                    f.write(
                        f"""# Test File {i}

## Content
This is test file {i}.
"""
                    )

            results = parser.parse_directory(temp_dir, file_pattern="*.md")

            assert len(results) == 3
            for result in results:
                assert "title" in result
                assert "sections" in result
                assert "Content" in result["sections"]
                assert "file_path" in result
                assert "file_name" in result

    def test_content_type_inference(self):
        """Test content type inference."""
        parser = RegexParser()

        # Rule content
        rule_content = """# Test Rule

## Rule Relationship
This rule relates to something.
"""
        assert parser.infer_content_type(rule_content) == "rule"

        # Document content
        doc_content = """# Test Document

## Diagrams
```mermaid
graph TD;
    A-->B;
    A-->C;
```
"""
        assert parser.infer_content_type(doc_content) == "document"

        # Generic content
        generic_content = "Just some plain text."
        assert parser.infer_content_type(generic_content) == "generic"

        # Inference from file path
        assert parser.infer_content_type("content", Path("test.mdc")) == "rule"
        assert parser.infer_content_type("content", Path("test.md")) == "document"
