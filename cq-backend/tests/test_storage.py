import pytest

from cq_backend.domain.application import Application
from cq_backend.errors import BackendError
from cq_backend.storage.zova import ZovaStorage


@pytest.mark.asyncio
async def test_zova_round_trip_survives_reopen(tmp_path):
    path = tmp_path / "applications.zova"
    storage = ZovaStorage(path)
    await storage.open()
    application = Application()
    await storage.save_application(application, expected_revision=0)
    await storage.close()
    reopened = ZovaStorage(path)
    await reopened.open()
    loaded = await reopened.get_application(application.application_id)
    assert loaded == application
    assert await reopened.list_applications() == [application]
    await reopened.close()


@pytest.mark.asyncio
async def test_output_and_application_updates_roll_back_together(tmp_path):
    storage = ZovaStorage(tmp_path / "applications.zova")
    await storage.open()
    try:
        first, second = Application(), Application()
        for app in (first, second):
            await storage.save_application(app, expected_revision=0)
        first.revision = 2
        first.queue_run_id = "queue-run"
        second.revision = 3  # Simulate a stale snapshot after another correction.
        with pytest.raises(BackendError):
            await storage.save_output("queue-run", "queue", "{}", [first, second])
        assert (await storage.get_application(first.application_id)).revision == 1
        assert (
            await storage.get_application(first.application_id)
        ).queue_run_id is None
        with pytest.raises(BackendError) as error:
            await storage.get_output("queue")
        assert error.value.code == "NOT_FOUND"
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_stale_write_does_not_overwrite_existing_state(tmp_path):
    storage = ZovaStorage(tmp_path / "applications.zova")
    await storage.open()
    application = Application()
    await storage.save_application(application, expected_revision=0)
    stale = application.model_copy(deep=True)
    application.revision += 1
    await storage.save_application(application, expected_revision=1)
    stale.error = "overwrite"
    with pytest.raises(BackendError) as error:
        await storage.save_application(stale, expected_revision=1)
    assert error.value.code == "STALE_REVISION"
    assert (await storage.get_application(application.application_id)).error is None
    await storage.close()
