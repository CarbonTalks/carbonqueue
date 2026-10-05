import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import zova

from cq_backend.domain.application import Application
from cq_backend.errors import BackendError


class ZovaStorage:
    """All native handles stay on one dedicated thread (Zova handles are unsendable)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="zova")
        self._db = None

    async def _call(self, function, *args):
        def invoke():
            # Never carry native handles in exception traceback frames across threads.
            try:
                return True, function(*args)
            except BackendError as error:
                return False, (
                    error.code,
                    error.message,
                    error.status_code,
                    error.application_id,
                )
            except Exception as error:  # noqa: BLE001 -- contain native tracebacks on their owning thread
                logging.getLogger("cq_backend.storage").error(
                    "Zova operation failed (%s)", type(error).__name__
                )
                return False, (
                    "PERSISTENCE_FAILURE",
                    "Unable to access persisted state",
                    503,
                    None,
                )

        success, result = await asyncio.get_running_loop().run_in_executor(
            self._executor, invoke
        )
        if not success:
            raise BackendError(*result)
        return result

    async def open(self) -> None:
        await self._call(self._open)

    def _open(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = (
            zova.Database.open(str(self.path))
            if self.path.exists()
            else zova.Database.create(str(self.path))
        )
        self._db.set_busy_timeout(5000)
        self._db.exec(
            "CREATE TABLE IF NOT EXISTS applications (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, payload TEXT NOT NULL)"
        )
        self._db.exec(
            "CREATE TABLE IF NOT EXISTS outputs (id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL, sequence INTEGER NOT NULL)"
        )

    async def close(self) -> None:
        if self._db is not None:
            await self._call(self._close)
        self._executor.shutdown(wait=True)

    def _close(self) -> None:
        self._db.close()
        self._db = None

    async def save_application(
        self, application: Application, *, expected_revision: int
    ) -> None:
        await self._call(
            self._save_application, application.model_copy(deep=True), expected_revision
        )

    def _save_application(
        self, application: Application, expected_revision: int
    ) -> None:
        if application.revision != expected_revision + 1:
            raise BackendError(
                "STALE_REVISION", "Application revision has changed", 409
            )
        if expected_revision == 0:
            sql = "INSERT INTO applications(id, revision, payload) VALUES (?1, ?2, ?3)"
        else:
            sql = "UPDATE applications SET revision = ?2, payload = ?3 WHERE id = ?1 AND revision = ?4"
        with self._db.prepare(sql) as statement:
            statement.bind_text(1, application.application_id)
            statement.bind_int(2, application.revision)
            statement.bind_text(3, application.model_dump_json())
            if expected_revision:
                statement.bind_int(4, expected_revision)
            statement.step()
        if self._db.changes() != 1:
            raise BackendError(
                "STALE_REVISION", "Application revision has changed", 409
            )

    async def get_application(self, application_id: str) -> Application:
        return await self._call(self._get_application, application_id)

    def _get_application(self, application_id: str) -> Application:
        with self._db.prepare(
            "SELECT payload FROM applications WHERE id = ?1"
        ) as statement:
            statement.bind_text(1, application_id)
            if statement.step() != zova.Step.ROW:
                raise BackendError("NOT_FOUND", "Application not found", 404)
            return Application.model_validate_json(statement.column_text(0))

    async def list_applications(self) -> list[Application]:
        return await self._call(self._list_applications)

    def _list_applications(self) -> list[Application]:
        applications = []
        with self._db.prepare(
            "SELECT payload FROM applications ORDER BY rowid"
        ) as statement:
            while statement.step() == zova.Step.ROW:
                applications.append(
                    Application.model_validate_json(statement.column_text(0))
                )
        return applications

    async def save_output(
        self, output_id: str, kind: str, payload: str, applications: list[Application]
    ) -> None:
        await self._call(self._save_output, output_id, kind, payload, applications)

    def _save_output(
        self, output_id: str, kind: str, payload: str, applications: list[Application]
    ) -> None:
        self._db.begin_immediate()
        try:
            for application in applications:
                self._save_application(application, application.revision - 1)
            with self._db.prepare(
                "INSERT INTO outputs(id, kind, payload, sequence) VALUES (?1, ?2, ?3, (SELECT COALESCE(MAX(sequence), 0) + 1 FROM outputs))"
            ) as statement:
                for index, value in enumerate((output_id, kind, payload), 1):
                    statement.bind_text(index, value)
                statement.step()
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

    async def get_output(self, kind: str, output_id: str | None = None) -> str:
        return await self._call(self._get_output, kind, output_id)

    def _get_output(self, kind: str, output_id: str | None) -> str:
        sql = "SELECT payload FROM outputs WHERE kind = ?1"
        sql += " AND id = ?2" if output_id else " ORDER BY sequence DESC LIMIT 1"
        with self._db.prepare(sql) as statement:
            statement.bind_text(1, kind)
            if output_id:
                statement.bind_text(2, output_id)
            if statement.step() != zova.Step.ROW:
                raise BackendError("NOT_FOUND", "Result not found", 404)
            return statement.column_text(0)
