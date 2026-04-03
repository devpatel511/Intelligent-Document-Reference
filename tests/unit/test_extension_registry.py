"""Tests for ingestion extension registry consistency."""

import inspect

from ingestion.crawler import crawl_directory
from ingestion.extension_registry import (
    AUDIO_FILE_EXTENSIONS,
    CODE_FILE_EXTENSIONS,
    DOCUMENT_FILE_EXTENSIONS,
    IMAGE_FILE_EXTENSIONS,
    SUPPORTED_FILE_EXTENSIONS,
)
from ingestion.pipeline import PipelineConfig


def test_supported_extension_union_consistent() -> None:
    """SUPPORTED_FILE_EXTENSIONS is the union of category sets."""
    expected = (
        AUDIO_FILE_EXTENSIONS
        | CODE_FILE_EXTENSIONS
        | DOCUMENT_FILE_EXTENSIONS
        | IMAGE_FILE_EXTENSIONS
    )
    assert set(SUPPORTED_FILE_EXTENSIONS) == expected


def test_pipeline_config_uses_canonical_extensions() -> None:
    """PipelineConfig defaults to the canonical extension list."""
    assert set(PipelineConfig().supported_extensions) == set(SUPPORTED_FILE_EXTENSIONS)


def test_crawler_default_uses_canonical_extensions() -> None:
    """Crawler default filter list stays in sync with canonical extensions."""
    signature = inspect.signature(crawl_directory)
    default_value = signature.parameters["supported_extensions"].default
    assert set(default_value) == set(SUPPORTED_FILE_EXTENSIONS)
