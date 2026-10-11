"""Opt-in safety check using the supplied public PDFs, with no LLM calls."""

import os
from pathlib import Path

import pypdfium2
import pytest
from litestar.testing import TestClient
from test_api import BrokenML, Engine

from cq_backend.app import create_app
from cq_backend.config import Settings
from cq_backend.domain.application import (
    Evidence,
    ExtractedField,
    ParsedDocument,
    ParsedPage,
)


class PDFTextParser:
    async def parse(self, document_id, path):
        pages = []
        with pypdfium2.PdfDocument(path) as pdf:
            for index in range(len(pdf)):
                page = pdf[index]
                text = page.get_textpage()
                try:
                    pages.append(
                        ParsedPage(
                            number=index + 1,
                            text=" ".join(text.get_text_range().split()),
                        )
                    )
                finally:
                    text.close()
                    page.close()
        return ParsedDocument(document_id=document_id, pages=pages)


class WrongCapacityExtractor:
    async def extract(self, documents):
        statement = next(
            doc
            for doc in documents
            if any("Construction of an 8MW solar" in page.text for page in doc.pages)
        )
        observations = []
        for value, page_number, quote in [
            (8, 8, "Construction of an 8MW solar photovoltaic park"),
            (5, 11, "5MW connection"),
        ]:
            evidence = [
                Evidence(
                    document_id=statement.document_id, page=page_number, quote=quote
                )
            ]
            observations.append(
                ExtractedField(
                    field="capacity_mw",
                    value=value,
                    unit="MW",
                    confidence=0.99,
                    capacity_scope="proposed_project",
                    evidence=evidence,
                )
            )
        observations.append(
            ExtractedField(
                field="technology",
                value="solar",
                confidence=0.99,
                evidence=[
                    Evidence(
                        document_id=statement.document_id,
                        page=8,
                        quote="solar photovoltaic park",
                    )
                ],
            )
        )
        return observations


@pytest.mark.skipif(
    not os.getenv("CQ_DEMO_DOCS"),
    reason="Set CQ_DEMO_DOCS to the supplied demo document directory",
)
def test_real_arncott_pdf_trap_numbers_require_human_review(tmp_path):
    paths = sorted((Path(os.environ["CQ_DEMO_DOCS"]) / "B_arncott_solar").glob("*.pdf"))
    assert len(paths) == 3
    with TestClient(
        create_app(
            Settings(data_dir=tmp_path),
            parser=PDFTextParser(),
            extractor=WrongCapacityExtractor(),
            ml=BrokenML(),
            queue_engine=Engine(),
        )
    ) as client:
        response = client.post(
            "/applications/extract",
            files=[
                ("files", (path.name, path.read_bytes(), "application/pdf"))
                for path in paths
            ],
        )
        assert response.status_code == 201, response.text
        application = response.json()
        assert application["status"] == "NEEDS_REVIEW"
        assert application["readiness"]["missing_fields"] == ["capacity_mw"]
        assert application["project_features"] is None
        assert application["prediction"] is None
        assert [item["value"] for item in application["observations"][:2]] == [8, 5]
        corrected = client.patch(
            f"/applications/{application['application_id']}/observations",
            json={
                "actor": "reviewer",
                "expected_revision": application["revision"],
                "values": {"capacity_mw": 20},
                "reason": "Test correction only; not a factual Arncott capacity",
            },
        )
        assert corrected.status_code == 200, corrected.text
        assert corrected.json()["status"] == "READY"
