#!/usr/bin/env python
"""
Synchronize rules and documents to Basic Memory.

This script can be used manually or as part of a GitHub Action workflow.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# Add the project directory to the Python path
project_dir = Path(__file__).parent.parent.parent
sys.path.append(str(project_dir))

from src.status.sync.sync_orchestrator import SyncOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("sync_script")


async def main(file_paths: Optional[List[str]] = None, content_type: Optional[str] = None) -> None:
    """
    Synchronize files to Basic Memory.

    Args:
        file_paths: List of file paths to sync, or None to sync all
        content_type: Optional content type to sync ("rule", "document", or None for all)
    """
    logger.info(f"Starting synchronization to Basic Memory...")

    # Initialize sync orchestrator
    sync_orchestrator = SyncOrchestrator()

    # Synchronize files
    if content_type:
        logger.info(f"Syncing {content_type} content...")
        result = await sync_orchestrator.sync_by_type(content_type, file_paths)
    else:
        logger.info("Syncing all content...")
        result = await sync_orchestrator.orchestrate_sync(file_paths)

    # Print results
    logger.info("\nSynchronization complete!")

    if "rules" in result:
        logger.info(f"Rules: Synced {result['rules']['synced_count']} / {result['rules']['total_count']}")

    if "documents" in result:
        logger.info(f"Documents: Synced {result['documents']['synced_count']} / {result['documents']['total_count']}")

    logger.info(f"Total: Synced {result.get('total_synced', 0)} files")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Synchronize files to Basic Memory")
    parser.add_argument("--files", type=str, help="Space-separated list of file paths to sync")
    parser.add_argument("--type", type=str, choices=["rule", "document"], help="Content type to sync")
    args = parser.parse_args()

    # Parse file list
    file_paths = args.files.split() if args.files else None

    # Run synchronization
    asyncio.run(main(file_paths, args.type))
