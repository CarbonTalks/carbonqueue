import os

from cq_backend.config import Settings


def test_dotenv_loads_gemini_key_and_model(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(os, "environ", {})
    (tmp_path / ".env").write_text(
        "GOOGLE_API_KEY=test-key-not-real\n"
        "CQ_EXTRACTION_MODEL=google:gemini-3.8-flash\n"
        "CQ_DATA_DIR=state\n"
    )
    settings = Settings.from_env()
    assert settings.extraction_model == "google:gemini-3.8-flash"
    assert str(settings.data_dir) == "state"
    assert os.environ["GOOGLE_API_KEY"] == "test-key-not-real"


def test_process_environment_takes_precedence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        os,
        "environ",
        {
            "GOOGLE_API_KEY": "process-test-key",
            "CQ_EXTRACTION_MODEL": "google:process-model",
        },
    )
    (tmp_path / ".env").write_text(
        "GOOGLE_API_KEY=file-test-key\nCQ_EXTRACTION_MODEL=google:file-model\n"
    )
    settings = Settings.from_env()
    assert settings.extraction_model == "google:process-model"
    assert os.environ["GOOGLE_API_KEY"] == "process-test-key"


def test_no_dotenv_keeps_extraction_disabled(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(os, "environ", {})
    assert Settings.from_env().extraction_model is None


def test_gemini_agent_constructs_without_network_calls(monkeypatch):
    from cq_backend.agent.extract import ExtractionAgent

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-real")
    agent = ExtractionAgent("google:gemini-3.8-flash")
    assert agent.agent.model.model_name == "gemini-3.8-flash"
