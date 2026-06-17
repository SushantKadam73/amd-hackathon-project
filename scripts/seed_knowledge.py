#!/usr/bin/env python
"""GRC Platform - Knowledge Base Seeding Script.

Pre-loads the knowledge base with framework-specific compliance information
for NIST SP 800-53 controls (PE-03, AC-02, SC-07, IR-06, RA-05).

This script:
1. Clears any existing pre-loaded knowledge
2. Generates embeddings for each knowledge entry
3. Stores entries in the knowledge_base table

Run with:
    cd project_root && python scripts/seed_knowledge.py
"""

import logging
import os
import sys
import time
from typing import Any, Optional

# Ensure project root is in the Python path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def check_database() -> bool:
    """Verify the database connection and that required tables exist.

    Returns:
        bool: True if database is ready.
    """
    try:
        from api.database import count_knowledge_entries, get_cursor  # noqa: WPS433

        with get_cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'knowledge_base'"
            )
            exists = cur.fetchone() is not None

        if not exists:
            logger.error(
                "knowledge_base table does not exist. "
                "Run 'python scripts/init_db.py' first."
            )
            return False

        count = count_knowledge_entries()
        logger.info(f"Current knowledge base entries: {count}")
        return True

    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False


def seed_knowledge_base(
    clear_existing: bool = True,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    """Seed the knowledge base with pre-loaded compliance information.

    Args:
        clear_existing: If True, clear existing pre-loaded entries first.
        user_id: Optional user ID for audit logging.

    Returns:
        dict: Summary of the seeding operation.

    Raises:
        RuntimeError: If seeding fails critically.
    """
    from rag.knowledge_loader import (  # noqa: WPS433
        get_preloaded_knowledge,
        load_preloaded_knowledge,
    )

    # Count entries to be loaded
    preloaded = get_preloaded_knowledge()
    logger.info(f"Found {len(preloaded)} pre-loaded knowledge entries")

    if clear_existing:
        try:
            from api.database import delete_knowledge_by_source  # noqa: WPS433

            deleted = delete_knowledge_by_source("Pre-loaded")
            logger.info(f"Cleared {deleted} existing pre-loaded entries")

            # Also clear framework research entries
            deleted2 = delete_knowledge_by_source("GRC Platform Framework Research")
            logger.info(f"Cleared {deleted2} existing framework research entries")
        except Exception as e:
            logger.warning(f"Could not clear existing entries: {e}")

    # Load the pre-loaded knowledge
    logger.info("Loading pre-loaded knowledge entries...")
    start_time = time.time()

    result = load_preloaded_knowledge(user_id=user_id)

    elapsed = time.time() - start_time
    logger.info(
        f"Seeding completed in {elapsed:.2f}s: "
        f"{result['loaded_count']} loaded, "
        f"{result['error_count']} errors"
    )

    if result["error_count"] > 0:
        for err in result["errors"][:5]:  # Show first 5 errors
            logger.warning(f"  - {err}")
        if result["error_count"] > 5:
            logger.warning(f"  ... and {result['error_count'] - 5} more errors")

    return result


def verify_seeding() -> dict[str, Any]:
    """Verify that seeding was successful by querying the database.

    Returns:
        dict: Verification results with entry counts per category.
    """
    from api.database import get_cursor  # noqa: WPS433

    verification: dict[str, Any] = {
        "total_entries": 0,
        "by_control": {},
        "by_category": {},
        "by_source": {},
        "has_embeddings": 0,
    }

    with get_cursor() as cur:
        # Total count
        cur.execute("SELECT COUNT(*) as cnt FROM knowledge_base")
        verification["total_entries"] = cur.fetchone()["cnt"]

        # Entries with embeddings
        cur.execute(
            "SELECT COUNT(*) as cnt FROM knowledge_base "
            "WHERE embedding_vector IS NOT NULL"
        )
        verification["has_embeddings"] = cur.fetchone()["cnt"]

        # By control_id
        cur.execute(
            "SELECT metadata->>'control_id' as control_id, COUNT(*) as cnt "
            "FROM knowledge_base WHERE metadata->>'control_id' IS NOT NULL "
            "GROUP BY metadata->>'control_id' ORDER BY control_id"
        )
        for row in cur.fetchall():
            verification["by_control"][row["control_id"]] = row["cnt"]

        # By category
        cur.execute(
            "SELECT metadata->>'category' as category, COUNT(*) as cnt "
            "FROM knowledge_base WHERE metadata->>'category' IS NOT NULL "
            "GROUP BY metadata->>'category' ORDER BY category"
        )
        for row in cur.fetchall():
            verification["by_category"][row["category"]] = row["cnt"]

        # By source
        cur.execute(
            "SELECT source, COUNT(*) as cnt FROM knowledge_base "
            "GROUP BY source ORDER BY source"
        )
        for row in cur.fetchall():
            verification["by_source"][row["source"]] = row["cnt"]

    return verification


def main() -> None:
    """Main entry point for knowledge base seeding."""
    print("=" * 60)
    print("  GRC Platform - Knowledge Base Seeding")
    print("=" * 60)
    print()

    # Step 1: Check database
    print("[1/4] Checking database connection...")
    if not check_database():
        logger.error(
            "Database is not ready. Ensure PostgreSQL is running and "
            "'python scripts/init_db.py' has been executed."
        )
        sys.exit(1)
    print("  ✓ Database is ready")
    print()

    # Step 2: Seed the knowledge base
    print("[2/4] Seeding knowledge base...")
    try:
        result = seed_knowledge_base(clear_existing=True)
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)

    if result["error_count"] > 0:
        print(f"  ⚠ Completed with {result['error_count']} errors")
    else:
        print(f"  ✓ Loaded {result['loaded_count']} entries successfully")
    print()

    # Step 3: Verify seeding
    print("[3/4] Verifying knowledge base...")
    try:
        verification = verify_seeding()
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)

    print(f"  Total entries: {verification['total_entries']}")
    print(f"  Entries with embeddings: {verification['has_embeddings']}")

    if verification["by_control"]:
        print("  By control:")
        for ctrl_ref, count in sorted(verification["by_control"].items()):
            print(f"    - {ctrl_ref}: {count}")
    if verification["by_category"]:
        print("  By category:")
        for cat, count in sorted(verification["by_category"].items()):
            print(f"    - {cat}: {count}")
    if verification["by_source"]:
        print("  By source:")
        for src, count in sorted(verification["by_source"].items()):
            print(f"    - {src}: {count}")
    print()

    # Step 4: Summary
    print("[4/4] Summary")
    if verification["has_embeddings"] == verification["total_entries"]:
        print("  ✓ All entries have valid embeddings")
    else:
        print(
            f"  ⚠ {verification['total_entries'] - verification['has_embeddings']} "
            "entries missing embeddings"
        )

    if verification["total_entries"] > 0:
        print("\n✅ Knowledge base seeding completed successfully!")
    else:
        print("\n⚠️  Knowledge base is empty after seeding!")
        sys.exit(1)


if __name__ == "__main__":
    main()
