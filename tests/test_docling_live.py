import os

import pytest
from litestar.testing import TestClient
from pydantic_ai.models.test import TestModel

from cq_backend.agent.extract import ExtractionAgent
from cq_backend.app import create_app
from cq_backend.config import Settings


@pytest.mark.skipif(
    os.getenv("CQ_TEST_DOCLING") != "1",
    reason="Enable CQ_TEST_DOCLING=1 to load/download real Docling models",
)
def test_real_pdf_docling_agent_and_zova_end_to_end(tmp_path, planning_pdf):
    # TestModel replaces only the paid LLM boundary; real Docling and Zova run.
    class EvidenceModelAgent:
        async def extract(self, documents):
            doc = documents[0]
            quote = "Solar development - capacity 12 MW"
            model = TestModel(
                custom_output_args={
                    "observations": [
                        {
                            "field": "technology",
                            "value": "solar",
                            "confidence": 0.99,
                            "evidence": [
                                {
                                    "document_id": doc.document_id,
                                    "page": 1,
                                    "quote": quote,
                                }
                            ],
                        },
                        {
                            "field": "capacity_mw",
                            "value": 12,
                            "unit": "MW",
                            "confidence": 0.99,
                            "evidence": [
                                {
                                    "document_id": doc.document_id,
                                    "page": 1,
                                    "quote": quote,
                                }
                            ],
                        },
                    ]
                }
            )
            return await ExtractionAgent(model).extract(documents)

    with TestClient(
        create_app(
            Settings(data_dir=tmp_path / "state"), extractor=EvidenceModelAgent()
        )
    ) as client:
        response = client.post(
            "/applications/extract",
            files={
                "files": ("planning.pdf", planning_pdf.read_bytes(), "application/pdf")
            },
        )
        assert response.status_code == 201, response.text
        app = response.json()
        assert app["status"] == "READY"
        assert "Solar development" in app["parsed_documents"][0]["pages"][0]["text"]
    with TestClient(create_app(Settings(data_dir=tmp_path / "state"))) as reopened:
        assert reopened.get(f"/applications/{app['application_id']}").json() == app
