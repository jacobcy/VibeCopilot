import pytest

from src.rule_engine.parser import _normalize_key, _parse_list_items, _parse_markdown_sections, _split_front_matter, parse_rule_content


class TestRuleParser:
    def test_split_front_matter(self):
        """Test splitting front matter from markdown content."""
        content = """---
title: Test Rule
type: test
---
# Test Rule

## Description
This is a test rule.

## Steps
1. Step 1
2. Step 2
"""
        front_matter, markdown = _split_front_matter(content)
        assert (
            front_matter.strip()
            == """title: Test Rule
type: test"""
        )
        assert markdown.strip().startswith("# Test Rule")

    def test_normalize_key(self):
        """Test normalizing section titles into valid keys."""
        assert _normalize_key("Test Key") == "test_key"
        assert _normalize_key("Complex Key With Spaces") == "complex_key_with_spaces"
        assert _normalize_key("already_normalized") == "already_normalized"
        assert _normalize_key("Mixed Case") == "mixed_case"

    def test_parse_markdown_sections(self):
        """Test parsing markdown sections."""
        markdown = """# Test Rule

## Description
This is a test rule.

## Steps
1. Step 1
2. Step 2

## Notes
Some notes here.
"""
        sections = _parse_markdown_sections(markdown)
        assert "description" in sections
        assert "steps" in sections
        assert "notes" in sections
        assert sections["description"].strip() == "This is a test rule."
        assert "Step 1" in sections["steps"]
        assert "Step 2" in sections["steps"]
        assert sections["notes"].strip() == "Some notes here."

    def test_parse_list_items(self):
        """Test parsing list items."""
        # Test markdown list
        markdown_list = """1. Item 1
2. Item 2
   - Subitem 1
3. Item 3"""
        items = _parse_list_items(markdown_list)
        assert len(items) == 3
        assert items[0]["content"] == "Item 1"
        assert items[1]["content"] == "Item 2\n   - Subitem 1"
        assert items[2]["content"] == "Item 3"

        # Test YAML list
        yaml_list = """- name: Item 1
  description: Description 1
- name: Item 2
  description: Description 2"""
        items = _parse_list_items(yaml_list)
        assert len(items) == 2
        assert items[0]["name"] == "Item 1"
        assert items[0]["description"] == "Description 1"
        assert items[1]["name"] == "Item 2"
        assert items[1]["description"] == "Description 2"

    def test_parse_rule_content_complete(self):
        """Test complete parsing of rule content."""
        content = """---
title: Test Rule
type: test
priority: high
---
# Test Rule

## Description
This is a test rule.

## Steps
1. Step 1
2. Step 2

## Examples
- name: Example 1
  code: |
    def test():
        pass
- name: Example 2
  code: |
    def another_test():
        pass
"""
        result = parse_rule_content(content)

        # Test metadata
        assert result["metadata"]["title"] == "Test Rule"
        assert result["metadata"]["type"] == "test"
        assert result["metadata"]["priority"] == "high"

        # Test sections
        assert "description" in result["sections"]
        assert "steps" in result["sections"]
        assert "examples" in result["sections"]

        # Test examples parsing
        examples = _parse_list_items(result["sections"]["examples"])
        assert len(examples) == 2
        assert examples[0]["name"] == "Example 1"
        assert "def test():" in examples[0]["code"]
        assert examples[1]["name"] == "Example 2"
        assert "def another_test():" in examples[1]["code"]

    def test_rule_without_front_matter(self):
        """Test parsing a rule without front matter."""
        content = """# Test Rule

## Description
This is a test rule without front matter.
"""
        result = parse_rule_content(content)
        assert result["metadata"] == {}
        assert "description" in result["sections"]
        assert result["sections"]["description"].strip() == "This is a test rule without front matter."

    def test_empty_rule(self):
        """Test parsing an empty rule."""
        result = parse_rule_content("")
        assert result["metadata"] == {}
        assert result["sections"] == {}

    def test_rule_with_invalid_front_matter(self):
        """Test parsing a rule with invalid front matter."""
        content = """---
invalid: yaml:
  - missing
  closing
  quotes
---
# Test Rule
"""
        # Should not raise an exception, but log an error
        result = parse_rule_content(content)
        assert isinstance(result["metadata"], dict)
        # Even with invalid YAML, we should still get the markdown content
        assert "# Test Rule" in content
