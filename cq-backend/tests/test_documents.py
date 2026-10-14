import pytest
from litestar.datastructures import UploadFile

from cq_backend.documents.docling import DoclingParser
from cq_backend.errors import BackendError
from cq_backend.services.documents import DocumentService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name, data, code",
    [
        ("evil.txt", b"text", "UNSUPPORTED_FORMAT"),
        ("empty.pdf", b"", "INVALID_DOCUMENT"),
        ("big.pdf", b"%PDF" + b"x" * 100, "FILE_TOO_LARGE"),
        ("fake.pdf", b"not a pdf", "INVALID_DOCUMENT"),
    ],
)
async def test_invalid_uploads_are_rejected_without_writing(tmp_path, name, data, code):
    service = DocumentService(tmp_path, max_file_bytes=100)
    with pytest.raises(BackendError) as error:
        await service.ingest(
            [UploadFile(filename=name, content_type="application/pdf", file_data=data)]
        )
    assert error.value.code == code
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_multiple_files_use_generated_paths_not_client_filenames(tmp_path):
    service = DocumentService(tmp_path)
    metadata = await service.ingest(
        [
            UploadFile(
                filename="../../one.pdf",
                content_type="application/pdf",
                file_data=b"%PDF-1.7\nfirst",
            ),
            UploadFile(
                filename="one.pdf",
                content_type="application/pdf",
                file_data=b"%PDF-1.7\nsecond",
            ),
        ]
    )
    assert len(metadata) == 2
    assert metadata[0].filename == "one.pdf"
    assert metadata[0].storage_reference != metadata[1].storage_reference
    assert all((tmp_path / doc.storage_reference).is_file() for doc in metadata)


@pytest.mark.asyncio
async def test_malformed_pdf_is_a_parse_error(tmp_path):
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"%PDF-1.7\nbroken")
    with pytest.raises(BackendError) as error:
        await DoclingParser().parse("doc", path)
    assert error.value.code == "PARSE_FAILED"


def test_docling_normalization_preserves_pages_tables_headings_and_bounds():
    from docling_core.types.doc import (
        BoundingBox,
        DocItemLabel,
        DoclingDocument,
        ProvenanceItem,
        Size,
        TableCell,
        TableData,
    )

    doc = DoclingDocument(name="test")
    doc.add_page(page_no=1, size=Size(width=100, height=100))
    doc.add_page(page_no=2, size=Size(width=100, height=100))
    doc.add_text(
        label=DocItemLabel.SECTION_HEADER,
        text="Solar 12 MW",
        prov=ProvenanceItem(
            page_no=1, bbox=BoundingBox(l=1, t=2, r=90, b=20), charspan=(0, 11)
        ),
    )
    parsed = DoclingParser.normalize("doc", doc)
    assert parsed.pages[0].text == "Solar 12 MW"
    assert parsed.pages[0].blocks[0].kind == "section_header"
    assert parsed.pages[0].blocks[0].bbox["l"] == 1
    doc.add_table(
        data=TableData(
            num_rows=1,
            num_cols=1,
            table_cells=[
                TableCell(
                    start_row_offset_idx=0,
                    end_row_offset_idx=1,
                    start_col_offset_idx=0,
                    end_col_offset_idx=1,
                    text="12 MW",
                )
            ],
        ),
        prov=ProvenanceItem(
            page_no=2, bbox=BoundingBox(l=1, t=2, r=90, b=20), charspan=(0, 5)
        ),
    )
    parsed = DoclingParser.normalize("doc", doc)
    assert len(parsed.pages) == 2
    assert "12 MW" in parsed.pages[1].tables[0]
    assert parsed.pages[1].blocks[0].kind == "table"
