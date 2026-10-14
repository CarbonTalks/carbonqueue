import asyncio
from pathlib import Path
from typing import Protocol

from cq_backend.domain.application import ParsedBlock, ParsedDocument, ParsedPage
from cq_backend.errors import BackendError


class DocumentParser(Protocol):
    async def parse(self, document_id: str, path: Path) -> ParsedDocument: ...


class DoclingParser:
    def __init__(self, max_pages: int = 200):
        self.max_pages = max_pages

    async def parse(self, document_id: str, path: Path) -> ParsedDocument:
        return await asyncio.to_thread(self._parse, document_id, path)

    def _parse(self, document_id: str, path: Path) -> ParsedDocument:
        import pypdfium2
        from docling.datamodel.base_models import ConversionStatus
        from docling.document_converter import DocumentConverter

        try:
            # Reject malformed and excessive inputs before loading Docling models.
            with pypdfium2.PdfDocument(path) as pdf:
                if not 0 < len(pdf) <= self.max_pages:
                    raise BackendError(
                        "PAGE_LIMIT", "PDF exceeds the configured page limit", 400
                    )
            result = DocumentConverter().convert(
                path, max_num_pages=self.max_pages, raises_on_error=True
            )
            if result.status != ConversionStatus.SUCCESS:
                raise BackendError(
                    "PARSE_FAILED", "PDF could not be completely parsed", 422
                )
            parsed = self.normalize(document_id, result.document)
            if not any(page.text.strip() for page in parsed.pages):
                raise BackendError(
                    "PARSE_FAILED", "PDF contains no extractable text", 422
                )
            return parsed
        except BackendError:
            raise
        except Exception as error:
            raise BackendError("PARSE_FAILED", "Unable to parse PDF", 422) from error

    @staticmethod
    def normalize(document_id: str, document) -> ParsedDocument:
        from docling_core.types.doc import TableItem

        pages = {
            number: ParsedPage(number=number, text="") for number in document.pages
        }
        for item, _ in document.iterate_items():
            text = (
                item.export_to_markdown(doc=document)
                if isinstance(item, TableItem)
                else getattr(item, "text", "")
            )
            if not text:
                continue
            for provenance in item.prov:
                page = pages.setdefault(
                    provenance.page_no, ParsedPage(number=provenance.page_no, text="")
                )
                page.blocks.append(
                    ParsedBlock(
                        text=text,
                        kind=item.label.value,
                        bbox=provenance.bbox.model_dump(mode="json"),
                    )
                )
                page.text = "\n".join(filter(None, (page.text, text)))
                if isinstance(item, TableItem):
                    page.tables.append(text)
        return ParsedDocument(
            document_id=document_id, pages=[pages[number] for number in sorted(pages)]
        )
