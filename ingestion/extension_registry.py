"""Canonical file-extension registry for ingestion and file-status filtering."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

# Code, markup-as-code, and machine-readable config (indexed as CODE modality).
CODE_FILE_EXTENSIONS = frozenset(
    {
        ".py",
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".kt",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".scala",
        ".r",
        ".sql",
        ".sh",
        ".bash",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".ini",
        ".cfg",
        ".html",
        ".css",
        ".scss",
        ".vue",
        ".svelte",
    }
)

IMAGE_FILE_EXTENSIONS = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
)

AUDIO_FILE_EXTENSIONS = frozenset(
    {
        ".mp3",
        ".wav",
        ".m4a",
        ".aac",
        ".flac",
        ".ogg",
        ".oga",
        ".opus",
        ".webm",
        ".aiff",
        ".aif",
    }
)

DOCUMENT_FILE_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".txt",
        ".md",
        ".rst",
        ".csv",
        ".xlsx",
        ".xls",
        ".docx",
    }
)

SPREADSHEET_FILE_EXTENSIONS = frozenset({".xlsx", ".xls"})

EXTENSIONLESS_TEXT_FILENAMES = frozenset(
    {
        "dockerfile",
        "makefile",
        "jenkinsfile",
        "procfile",
        "gemfile",
        "rakefile",
        "license",
        "readme",
        "changelog",
        "codeowners",
    }
)

SUPPORTED_FILE_EXTENSIONS = tuple(
    sorted(
        DOCUMENT_FILE_EXTENSIONS
        | CODE_FILE_EXTENSIONS
        | IMAGE_FILE_EXTENSIONS
        | AUDIO_FILE_EXTENSIONS
    )
)


def is_extensionless_text_filename(filename: str) -> bool:
    """Return True when filename is an allowlisted extensionless text file."""
    lowered = filename.lower()
    if lowered in EXTENSIONLESS_TEXT_FILENAMES:
        return True
    return lowered.startswith(".env.")


def is_supported_path(
    path: Path,
    supported_extensions: Iterable[str] = SUPPORTED_FILE_EXTENSIONS,
) -> bool:
    """Return True when a path is supported by extension or extensionless allowlist."""
    ext = path.suffix.lower()
    if ext:
        return ext in frozenset(supported_extensions)
    return is_extensionless_text_filename(path.name)
