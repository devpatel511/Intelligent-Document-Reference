"""Integration tests for the UnifiedDatabase module."""

import uuid
from pathlib import Path
from typing import Generator, List

import pytest

from db import UnifiedDatabase


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Provide a temporary database path.

    Args:
        tmp_path: Pytest's temporary directory fixture.

    Returns:
        String path to the temporary database file.
    """
    return str(tmp_path / "test_unified_integration.db")


@pytest.fixture
def db(db_path: str) -> Generator[UnifiedDatabase, None, None]:
    """Provide an initialized UnifiedDatabase instance.

    Args:
        db_path: Path to the database file.

    Yields:
        Initialized UnifiedDatabase instance.
    """
    database = UnifiedDatabase(db_path)
    yield database


@pytest.fixture
def fake_vector() -> List[float]:
    """Provide a consistent fake vector for testing.

    Returns:
        List of 3072 float values for testing vector operations.
    """
    return [0.1] * 3072


def test_simple_integration(db: UnifiedDatabase, fake_vector: List[float]) -> None:
    """Run a simple integration test for the UnifiedDatabase module.

    This test:
    1. Registers a file.
    2. Creates a version.
    3. Adds a document chunk and its vector.
    4. Searches for the vector and verifies the result.

    Args:
        db: UnifiedDatabase instance fixture.
        fake_vector: Test vector fixture.
    """
    file_id = db.register_file("docs/intro.txt", "hash123", 3072, 0.0)

    version_id = db.create_version(file_id, "v1_hash")

    chunk_id = str(uuid.uuid4())

    chunks = [
        {
            "id": chunk_id,
            "chunk_index": 0,
            "start_offset": 0,
            "end_offset": 100,
            "text_content": "Hello world this is a test chunk.",
        }
    ]

    db.add_document(file_id, version_id, chunks, [fake_vector])

    results = db.search(fake_vector, limit=1)

    assert len(results) == 1
    assert results[0]["chunk_id"] == chunk_id
    assert results[0]["text_content"] == "Hello world this is a test chunk."
