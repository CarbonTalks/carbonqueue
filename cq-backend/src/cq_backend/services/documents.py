import asyncio
import hashlib
from pathlib import Path

from litestar.datastructures import UploadFile

from cq_backend.domain.application import DocumentMetadata, new_id
from cq_backend.errors import BackendError


class DocumentService:
    def __init__(
        self, root: Path, max_file_bytes: int = 20 * 1024 * 1024, max_files: int = 10
    ):
        self.root = Path(root)
        self.max_file_bytes = max_file_bytes
        self.max_files = max_files

    async def ingest(self, files: list[UploadFile]) -> list[DocumentMetadata]:
        if not files or len(files) > self.max_files:
            raise BackendError(
                "INVALID_DOCUMENT_COUNT",
                f"Upload between 1 and {self.max_files} PDFs",
                400,
            )
        validated = []
        try:
            for upload in files:
                filename = Path((upload.filename or "").replace("\\", "/")).name
                if Path(filename).suffix.lower() != ".pdf":
                    raise BackendError(
                        "UNSUPPORTED_FORMAT", "Only PDF documents are supported", 415
                    )
                content = await upload.read(self.max_file_bytes + 1)
                if len(content) > self.max_file_bytes:
                    raise BackendError(
                        "FILE_TOO_LARGE",
                        "Document exceeds the configured upload limit",
                        413,
                    )
                if not content.startswith(b"%PDF-"):
                    raise BackendError(
                        "INVALID_DOCUMENT",
                        "Document is empty or lacks a PDF header",
                        400,
                    )
                document_id = new_id()
                metadata = DocumentMetadata(
                    document_id=document_id,
                    filename=filename,
                    media_type="application/pdf",
                    size_bytes=len(content),
                    sha256=hashlib.sha256(content).hexdigest(),
                    storage_reference=f"{document_id}.pdf",
                )
                validated.append((metadata, content))
        finally:
            for upload in files:
                await upload.close()
        written = []
        try:
            await asyncio.to_thread(self.root.mkdir, parents=True, exist_ok=True)
            for metadata, content in validated:
                path = self.root / metadata.storage_reference
                written.append(path)
                await asyncio.to_thread(path.write_bytes, content)
        except OSError as error:
            for path in written:
                await asyncio.to_thread(path.unlink, missing_ok=True)
            raise BackendError(
                "DOCUMENT_STORAGE_FAILURE", "Unable to store uploaded documents"
            ) from error
        return [metadata for metadata, _ in validated]

    async def remove(self, documents: list[DocumentMetadata]) -> None:
        for document in documents:
            await asyncio.to_thread(
                (self.root / document.storage_reference).unlink, missing_ok=True
            )
