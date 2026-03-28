"""Unit tests for the ingestion pipeline."""

from pathlib import Path

import pytest

from ingestion import (
    AudioInput,
    CodeInput,
    CSVInput,
    DOCXInput,
    IngestionConfig,
    SpreadsheetInput,
    TextInput,
    get_input_handler,
    is_supported_path,
    parse_and_prepare,
)
from ingestion.code_syntax import CodeSyntaxError
from ingestion.models import (
    BlockType,
    ContentBlock,
    ExtractionMethod,
    SourceModality,
    StructuredDocument,
)


def test_text_input_parses_file(tmp_path: Path) -> None:
    """TextInput parses plain text files."""
    f = tmp_path / "test.txt"
    f.write_text("Hello, world.\n\nSecond paragraph.", encoding="utf-8")

    doc = parse_and_prepare(TextInput(), str(f), config=IngestionConfig())
    assert isinstance(doc, StructuredDocument)
    assert doc.source_modality == SourceModality.TEXT
    assert len(doc.blocks) == 1
    assert doc.blocks[0].content == "Hello, world.\n\nSecond paragraph."
    assert doc.blocks[0].block_type == BlockType.PARAGRAPH
    assert doc.blocks[0].metadata.extraction_method == ExtractionMethod.NATIVE


def test_code_input_parses_file(tmp_path: Path) -> None:
    """CodeInput parses code files."""
    f = tmp_path / "test.py"
    f.write_text("def foo():\n    return 42", encoding="utf-8")

    doc = parse_and_prepare(CodeInput(), str(f), config=IngestionConfig())
    assert doc.source_modality == SourceModality.CODE
    assert len(doc.blocks) == 1
    assert doc.blocks[0].block_type == BlockType.CODE_BLOCK
    assert "def foo" in doc.blocks[0].content


def test_get_input_handler_selects_by_extension() -> None:
    """get_input_handler selects correct handler by extension."""
    assert type(get_input_handler("x.pdf")).__name__ == "PDFInput"
    assert type(get_input_handler("x.png")).__name__ == "ImageInput"
    assert type(get_input_handler("x.mp3")).__name__ == "AudioInput"
    assert type(get_input_handler("x.wav")).__name__ == "AudioInput"
    assert type(get_input_handler("x.py")).__name__ == "CodeInput"
    assert type(get_input_handler("x.txt")).__name__ == "TextInput"
    assert type(get_input_handler("x.md")).__name__ == "TextInput"
    assert type(get_input_handler("x.rst")).__name__ == "TextInput"
    assert type(get_input_handler("x.csv")).__name__ == "CSVInput"
    assert type(get_input_handler("x.xlsx")).__name__ == "SpreadsheetInput"
    assert type(get_input_handler("x.xls")).__name__ == "SpreadsheetInput"
    assert type(get_input_handler("x.docx")).__name__ == "DOCXInput"


def test_code_input_rejects_invalid_python(tmp_path: Path) -> None:
    """CodeInput raises CodeSyntaxError for invalid Python."""
    f = tmp_path / "bad.py"
    f.write_text("def broken(\n", encoding="utf-8")
    with pytest.raises(CodeSyntaxError, match="Python syntax error"):
        parse_and_prepare(CodeInput(), str(f), config=IngestionConfig())


def test_code_input_rejects_invalid_json(tmp_path: Path) -> None:
    """CodeInput raises CodeSyntaxError for invalid JSON."""
    f = tmp_path / "bad.json"
    f.write_text("{ not json ", encoding="utf-8")
    with pytest.raises(CodeSyntaxError, match="JSON parse error"):
        parse_and_prepare(CodeInput(), str(f), config=IngestionConfig())


def test_code_input_rejects_invalid_css(tmp_path: Path) -> None:
    """CodeInput raises CodeSyntaxError for invalid CSS."""
    f = tmp_path / "bad.css"
    # tinycss2 reports an error token for this malformed input
    f.write_text("###", encoding="utf-8")
    with pytest.raises(CodeSyntaxError, match="CSS parse error"):
        parse_and_prepare(CodeInput(), str(f), config=IngestionConfig())


def test_audio_input_transcribes_mp3(tmp_path: Path) -> None:
    """AudioInput transcribes MP3 files when the inference client supports audio."""

    class _DummyInferenceClient:
        def transcribe_audio(self, audio):
            assert isinstance(audio, str)
            return "hello from audio"

    f = tmp_path / "clip.mp3"
    # Parser only needs a readable file path; content is not decoded directly.
    f.write_bytes(b"ID3\x04\x00\x00\x00\x00\x00\x00")

    doc = parse_and_prepare(
        AudioInput(),
        str(f),
        config=IngestionConfig(),
        llm_client=_DummyInferenceClient(),
    )

    assert doc.source_modality == SourceModality.AUDIO
    assert len(doc.blocks) == 1
    assert doc.blocks[0].content == "hello from audio"
    assert doc.blocks[0].block_type == BlockType.PARAGRAPH
    assert doc.blocks[0].metadata.extraction_method == ExtractionMethod.LLM_ASSISTED


def test_csv_input_parses_table_blocks(tmp_path: Path) -> None:
    """CSVInput preserves tabular structure as table blocks."""
    f = tmp_path / "metrics.csv"
    f.write_text("name,value\nlatency,22\nthroughput,108", encoding="utf-8")

    doc = parse_and_prepare(CSVInput(), str(f), config=IngestionConfig())
    assert doc.source_modality == SourceModality.TEXT
    assert len(doc.blocks) >= 2
    assert doc.blocks[0].block_type == BlockType.PARAGRAPH
    assert "Table columns: name, value" in doc.blocks[0].content
    assert "Last row -> Row 2: name=throughput; value=108" in doc.blocks[0].content
    assert doc.blocks[1].block_type == BlockType.TABLE
    assert "Row 1: name=latency; value=22" in doc.blocks[1].content


def test_csv_pipe_delimited_parses_columns(tmp_path: Path) -> None:
    """CSVInput detects and parses pipe-delimited files."""
    f = tmp_path / "metrics_pipe.csv"
    f.write_text(
        "metric|value|unit\nlatency|22|ms\nthroughput|108|rps", encoding="utf-8"
    )

    doc = parse_and_prepare(CSVInput(), str(f), config=IngestionConfig())
    assert len(doc.blocks) >= 2
    assert "Table columns: metric, value, unit" in doc.blocks[0].content
    assert "Row 1: metric=latency; value=22; unit=ms" in doc.blocks[1].content


def test_spreadsheet_input_parses_xlsx(tmp_path: Path) -> None:
    """SpreadsheetInput parses .xlsx sheets into table blocks."""
    openpyxl = pytest.importorskip("openpyxl")
    f = tmp_path / "report.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["Metric", "Value"])
    ws.append(["Errors", 3])
    wb.save(f)

    doc = parse_and_prepare(SpreadsheetInput(), str(f), config=IngestionConfig())
    assert doc.source_modality == SourceModality.TEXT
    assert len(doc.blocks) >= 2
    assert doc.blocks[0].block_type == BlockType.PARAGRAPH
    table_block = next(
        block for block in doc.blocks if block.block_type == BlockType.TABLE
    )
    assert "Summary:sheet" in table_block.metadata.section_hierarchy
    assert "Rows 1-1" in table_block.content


def test_spreadsheet_input_fills_blank_headers(tmp_path: Path) -> None:
    """SpreadsheetInput normalizes blank/duplicate headers into stable keys."""
    openpyxl = pytest.importorskip("openpyxl")
    f = tmp_path / "blank_headers.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Budget"
    ws.append(["January", "", "", "March"])
    ws.append(["Income", "Item", "Category", "Income"])
    ws.append(["Bi-weekly", "Salary", "Essential", "Bonus"])
    wb.save(f)

    doc = parse_and_prepare(SpreadsheetInput(), str(f), config=IngestionConfig())
    assert any("Table columns:" in block.content for block in doc.blocks)
    summary = next(
        block
        for block in doc.blocks
        if block.block_type == BlockType.PARAGRAPH and "Table columns:" in block.content
    )
    assert "January" in summary.content
    assert "January_2" in summary.content or "column_" in summary.content


def test_spreadsheet_input_extracts_generic_side_panel_values(tmp_path: Path) -> None:
    """SpreadsheetInput includes generic adjacent-context numeric and ratio values."""
    openpyxl = pytest.importorskip("openpyxl")
    f = tmp_path / "distribution_panel.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "TEMPLATE"
    ws.append(["January", "", "", "", "", "", "", "", ""])
    ws.append(["Income", "", "", "", "", "Item", "Category", "Price", "Date"])
    ws.append(["Bi-weekly", 1000, "", "", "", "Rent", "Essential", 450, "2026-01-01"])
    ws.append(["Distribution", "", "", "", "", "Gas", "Essential", 120, "2026-01-02"])
    ws.append(["Essential", 0.45, 570, 450, "", "Gift", "Donation", 50, "2026-01-03"])
    ws.append(["Donation", 0.05, 520, 50, "", "Transfer", "Saving", 200, "2026-01-04"])
    ws.append(["Saving", 0.20, 320, 200, "", "Investment", "Liquid", 300, "2026-01-05"])
    ws.append(["Liquid", 0.30, 20, 300, "", "", "", "", ""])
    tab = openpyxl.worksheet.table.Table(displayName="JanExpenses", ref="F2:I8")
    ws.add_table(tab)
    wb.save(f)

    doc = parse_and_prepare(SpreadsheetInput(), str(f), config=IngestionConfig())
    summary = next(
        block
        for block in doc.blocks
        if block.block_type == BlockType.PARAGRAPH
        and "Table scope: spreadsheet > TEMPLATE:JanExpenses" in block.content
    )
    assert "Adjacent ratio values:" in summary.content
    assert "Essential (c2)=45.0%" in summary.content
    assert "Adjacent numeric/text context:" in summary.content


def test_docx_input_parses_text_and_tables(tmp_path: Path) -> None:
    """DOCXInput extracts headings, paragraphs, and tables."""
    docx = pytest.importorskip("docx")
    f = tmp_path / "brief.docx"

    d = docx.Document()
    d.add_heading("Quarterly Update", level=1)
    d.add_paragraph("Revenue increased quarter over quarter.")
    table = d.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Metric"
    table.rows[0].cells[1].text = "Value"
    table.rows[1].cells[0].text = "Revenue"
    table.rows[1].cells[1].text = "$10M"
    d.save(f)

    parsed = parse_and_prepare(DOCXInput(), str(f), config=IngestionConfig())
    assert parsed.source_modality == SourceModality.TEXT
    assert any(block.block_type == BlockType.HEADING for block in parsed.blocks)
    assert any(block.block_type == BlockType.TABLE for block in parsed.blocks)


def test_docx_input_extracts_embedded_image_text(tmp_path: Path) -> None:
    """DOCXInput reuses image parsing path for embedded images."""
    docx = pytest.importorskip("docx")
    pil_image = pytest.importorskip("PIL.Image")

    image_path = tmp_path / "inline.png"
    img = pil_image.new("RGB", (24, 24), color=(220, 10, 10))
    img.save(image_path)

    f = tmp_path / "with_image.docx"
    d = docx.Document()
    d.add_heading("Image Section", level=1)
    d.add_picture(str(image_path))
    d.save(f)

    class _VisionClient:
        def supports_image_input(self):
            return True

        def describe_image(self, _image, prompt=None):
            return "Embedded architecture diagram" if prompt is None else "architecture"

    parsed = parse_and_prepare(
        DOCXInput(),
        str(f),
        config=IngestionConfig(use_vision_for_images=True),
        llm_client=_VisionClient(),
    )

    assert any(
        block.block_type == BlockType.IMAGE_TEXT
        and "architecture" in block.content.lower()
        for block in parsed.blocks
    )


def test_extensionless_allowlist_supported() -> None:
    """Allowlisted extensionless files are considered supported."""
    assert is_supported_path(Path("Dockerfile")) is True


def test_preprocessing_normalizes_whitespace() -> None:
    """Preprocessing normalizes whitespace in blocks."""
    from ingestion.preprocessing import preprocess

    doc = StructuredDocument(
        source_id="test",
        blocks=[
            ContentBlock(
                content="  hello   world  \n\n  foo  ",
                block_type=BlockType.PARAGRAPH,
                source_modality=SourceModality.TEXT,
            )
        ],
        source_modality=SourceModality.TEXT,
    )
    result = preprocess(doc)
    assert len(result.blocks) == 1
    assert result.blocks[0].content == "hello world\n\nfoo"


def test_structured_document_serializable() -> None:
    """StructuredDocument can be serialized to dict."""
    doc = StructuredDocument(
        source_id="test",
        blocks=[
            ContentBlock(
                content="hello",
                block_type=BlockType.PARAGRAPH,
                source_modality=SourceModality.TEXT,
            )
        ],
        source_modality=SourceModality.TEXT,
    )
    d = doc.to_dict()
    assert d["source_id"] == "test"
    assert len(d["blocks"]) == 1
    assert d["blocks"][0]["content"] == "hello"


def test_chunk_document_produces_storeable_chunks() -> None:
    """Semantic chunker turns blocks into chunks and applies store heuristic."""
    from ingestion import chunk_document

    doc = StructuredDocument(
        source_id="test",
        blocks=[
            ContentBlock(
                content="Short.",
                block_type=BlockType.PARAGRAPH,
                source_modality=SourceModality.TEXT,
            ),
            ContentBlock(
                content="This is a longer paragraph with enough content to pass the heuristic.",
                block_type=BlockType.PARAGRAPH,
                source_modality=SourceModality.TEXT,
            ),
            ContentBlock(
                content="def foo():\n    return 42",
                block_type=BlockType.CODE_BLOCK,
                source_modality=SourceModality.CODE,
            ),
        ],
        source_modality=SourceModality.TEXT,
    )
    # Don't merge (min_block_chars > first block); lower min_chars_store so code block is kept
    chunks = chunk_document(
        doc,
        min_block_chars=100,
        max_block_chars=10_000,
        min_chars_store=10,
    )
    # Short paragraph filtered out; second paragraph and code block stored
    assert len(chunks) == 2
    assert "longer paragraph" in chunks[0]["text_content"]
    assert "def foo()" in chunks[1]["text_content"]
    assert all(
        "chunk_id" in c and "chunk_index" in c and "text_content" in c for c in chunks
    )


def test_should_store_chunk_heuristic() -> None:
    """Store heuristic filters by length and boilerplate."""
    from ingestion.chunking.semantic import CandidateChunk, should_store_chunk

    assert (
        should_store_chunk(
            CandidateChunk("Too short", (BlockType.PARAGRAPH,), 2, 0, 9),
            min_chars=30,
        )
        is False
    )
    assert (
        should_store_chunk(
            CandidateChunk(
                "A normal paragraph with enough words to pass the minimum length.",
                (BlockType.PARAGRAPH,),
                15,
                0,
                60,
            ),
            min_chars=30,
        )
        is True
    )
    assert (
        should_store_chunk(
            CandidateChunk("PAGE 1", (BlockType.PARAGRAPH,), 2, 0, 6),
            min_chars=3,
            skip_boilerplate=True,
        )
        is False
    )
