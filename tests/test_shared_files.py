import services.shared_files as shared_files

from types import SimpleNamespace

class FakeQuery:
    def __init__(self, rows=None):
        self._rows = rows if rows is not None else []
        self.inserted_payload = None

    def table(self, name):
            return self

    def insert(self, payload):
        self.inserted_payload = payload   # guarda lo que se iba a insertar
        return self

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self._rows)

class FakeFailingQuery(FakeQuery):
    def execute(self):
        raise RuntimeError("Query simulada fallida")

def test_save_shared_file_inserts_rows(monkeypatch):
    fake = FakeQuery()
    monkeypatch.setattr(shared_files, "get_admin_client", lambda: fake)
    result = shared_files.save_shared_file(
        json_data='{"a": 1}',
        analysis={"rows": 1},
        filename="ventas.xlsx",
        user_id="user-123",
        num_rows=10,
        num_columns=3,

    )
    assert result == {"success": True, "error": None}
    assert fake.inserted_payload["nombre_archivo"] == "ventas.xlsx"
    assert fake.inserted_payload["uploaded_by"] == "user-123"
    assert fake.inserted_payload["filas"] == 10

def test_save_shared_file_returns_error_on_failure(monkeypatch):
    monkeypatch.setattr(shared_files, "get_admin_client", lambda: FakeFailingQuery())

    result = shared_files.save_shared_file(
        "{}", {}, "x.xlsx", "u1", 1, 1
    )

    assert result["success"] is False
    assert result["error"] is not None

def test_list_shared_files_returns_rows(monkeypatch):
    rows = [
        {"id": 1, "nombre_archivo": "a.xlsx", "filas": 10}]
    monkeypatch.setattr(shared_files, "get_admin_client", lambda: FakeQuery(rows))

    assert shared_files.list_shared_files() == rows

def test_list_shared_files_empty(monkeypatch):
    monkeypatch.setattr(shared_files, "get_admin_client", lambda: FakeQuery(None))

    assert shared_files.list_shared_files() == []

def test_list_shared_files_on_failure_returns_empty(monkeypatch):
    monkeypatch.setattr(shared_files, "get_admin_client", lambda: FakeFailingQuery())

    assert shared_files.list_shared_files() == []

def test_get_shared_file_by_id_found(monkeypatch):
    row = {"id": 7, "dataframe_json": "{...}"}
    monkeypatch.setattr(
        shared_files, "get_admin_client", lambda: FakeQuery([row])
    )

    assert shared_files.get_shared_file_by_id(7) == row


def test_get_shared_file_by_id_not_found(monkeypatch):
    monkeypatch.setattr(
        shared_files, "get_admin_client", lambda: FakeQuery([])
    )

    assert shared_files.get_shared_file_by_id(999) is None


def test_get_shared_file_by_id_on_failure_returns_none(monkeypatch):
    monkeypatch.setattr(
        shared_files, "get_admin_client", lambda: FakeFailingQuery()
    )

    assert shared_files.get_shared_file_by_id(7) is None