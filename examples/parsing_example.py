#!/usr/bin/env python
"""
Example of using the unified parsing framework.

This example demonstrates how to use the parsing framework to:
1. Parse rule files
2. Parse document files
3. Extract entities from content
4. Store content in Basic Memory
"""

import asyncio
import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent.parent
sys.path.append(str(project_dir))

from src.memory.vector.memory_adapter import BasicMemoryAdapter
from src.parsing.parser_factory import create_parser
from src.parsing.processors.document_processor import DocumentProcessor
from src.parsing.processors.entity_processor import EntityProcessor
from src.parsing.processors.rule_processor import RuleProcessor


async def parse_rule_example():
    """Example of parsing a rule file."""
    print("\n=== Parsing Rule Example ===\n")

    # Create a rule processor with regex backend for simplicity
    rule_processor = RuleProcessor(backend="regex")

    # Path to a rule file
    rule_path = Path(".cursor/rules/core-rules/concept.mdc")

    if rule_path.exists():
        # Process the rule file
        rule_data = rule_processor.process_rule_file(rule_path)

        # Print rule information
        print(f"Rule: {rule_data.get('name')}")
        print(f"Description: {rule_data.get('description')}")
        print(f"Type: {rule_data.get('type')}")
        print(f"Valid: {rule_data.get('is_valid')}")

        # Print sections
        print("\nSections:")
        for section_name, content in rule_data.get("sections", {}).items():
            # Print first 50 characters of each section
            print(f"  - {section_name}: {content[:50]}...")
    else:
        print(f"Rule file not found: {rule_path}")


async def parse_document_example():
    """Example of parsing a document file."""
    print("\n=== Parsing Document Example ===\n")

    # Create a document processor with regex backend
    document_processor = DocumentProcessor(backend="regex")

    # Path to a document file
    doc_path = Path("docs/dev/architecture/content-parser-db-integration.md")

    if doc_path.exists():
        # Process the document file
        doc_data = document_processor.process_document_file(doc_path)

        # Print document information
        print(f"Document: {doc_data.get('title')}")
        print(f"Type: {doc_data.get('type')}")
        print(f"Valid: {doc_data.get('is_valid')}")

        # Print sections
        print("\nSections:")
        for section_name, content in list(doc_data.get("sections", {}).items())[:3]:
            # Print first 50 characters of first 3 sections
            print(f"  - {section_name}: {content[:50]}...")

        # Print code blocks
        print("\nCode Blocks:")
        for i, block in enumerate(doc_data.get("codeBlocks", [])[:2]):
            # Print first 50 characters of first 2 code blocks
            print(f"  - Block {i+1} ({block.get('language')}): {block.get('code', '')[:50]}...")
    else:
        print(f"Document file not found: {doc_path}")


async def extract_entities_example():
    """Example of extracting entities from content."""
    print("\n=== Entity Extraction Example ===\n")

    # Create an entity processor with regex backend
    entity_processor = EntityProcessor(backend="regex")

    # Sample content
    content = """
    # VibeCopilot Project Overview

    The VibeCopilot project is a demo project developed by the development team.
    It uses Python, React, and TypeScript as its main technologies.

    Claude API is used for AI integration, and SQLite for data storage.

    The project is hosted on GitHub and is managed by the project maintainers.
    """

    # Process content
    result = entity_processor.process_content(content)

    # Print extracted entities
    print("Extracted Entities:")
    for entity_id, entity_data in result.get("entities", {}).items():
        print(f"  - {entity_data.get('type', 'unknown')}: {entity_id}")
        # Print properties
        for key, value in entity_data.get("properties", {}).items():
            print(f"    - {key}: {value}")

    # Print relationships
    print("\nExtracted Relationships:")
    for rel in result.get("relationships", []):
        print(f"  - {rel.get('source')} {rel.get('type')} {rel.get('target')}")


async def basic_memory_example():
    """Example of storing content in Basic Memory."""
    print("\n=== Basic Memory Integration Example ===\n")

    # Create a Basic Memory adapter
    memory_adapter = BasicMemoryAdapter()

    # Sample content
    title = "Example Content"
    content = "This is an example of storing content in Basic Memory."

    # Store content
    print(f"Storing content: {title}")
    try:
        permalinks = await memory_adapter.store(
            [content],
            [
                {
                    "title": title,
                    "tags": "example,vibecopilot",
                    "example_id": "example1",
                    "created_at": "2023-05-01T12:00:00Z",
                }
            ],
            folder="examples",
        )

        if permalinks:
            print(f"Content stored successfully with permalink: {permalinks[0]}")

            # Search for the content
            print("\nSearching for the content...")
            results = await memory_adapter.search("example content", limit=1)

            if results:
                print(f"Found content: {results[0].get('title')}")
                print(f"Score: {results[0].get('score')}")

                # Get the content
                content_data = await memory_adapter.get(results[0].get("permalink"))
                if content_data:
                    print(f"Retrieved content title: {content_data.get('title')}")
                    print(f"Retrieved content metadata: {content_data.get('metadata')}")
            else:
                print("No search results found.")
        else:
            print("Failed to store content.")
    except Exception as e:
        print(f"Error: {str(e)}")


async def main():
    """Run examples."""
    print("=== Unified Parsing Framework Examples ===")

    # Parse rule example
    await parse_rule_example()

    # Parse document example
    await parse_document_example()

    # Extract entities example
    await extract_entities_example()

    # Basic Memory example
    try:
        await basic_memory_example()
    except Exception as e:
        print(f"\nBasic Memory example failed: {str(e)}")
        print("This might be because Basic Memory is not properly configured.")


if __name__ == "__main__":
    asyncio.run(main())
