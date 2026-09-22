"""
Pruebas de services/supabase_client.py, en particular la lectura del rol
desde public.profiles dentro de sign_in().

Estas pruebas mockean tanto el cliente de autenticación (get_client) como
el cliente admin (get_admin_client) -- NUNCA deben hacer una llamada de
red real. Antes de esta corrección, la lectura del rol vivía duplicada
directamente en app.py y SÍ hacía una llamada real a Supabase en cada
corrida de tests (confirmado viendo el log: una petición GET real a
.../rest/v1/profiles durante test_login_creates_authenticated_session).
"""

from types import SimpleNamespace

import pytest

import services.supabase_client as supabase_client


class FakeAuthUser:
    def __init__(self, user_id, email):
        self.id = user_id
        self.email = email


class FakeAuthResult:
    def __init__(self, user):
        self.user = user


class FakeQuery:
    """Simula la cadena .table().select().eq().limit().execute()."""

    def __init__(self, rows):
        self._rows = rows

    def table(self, name):
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
        raise RuntimeError("Fallo de red simulado")


@pytest.fixture(autouse=True)
def clear_client_caches():
    """
    get_client()/get_admin_client() usan @lru_cache: hay que limpiarlo
    entre pruebas para que cada una controle su propio mock.
    """
    supabase_client.get_client.cache_clear()
    supabase_client.get_admin_client.cache_clear()
    yield
    supabase_client.get_client.cache_clear()
    supabase_client.get_admin_client.cache_clear()


def _mock_auth_client(monkeypatch, user_id="user-123", email="ana@empresa.com"):
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_in_with_password=lambda creds: FakeAuthResult(
                FakeAuthUser(user_id, email)
            )
        )
    )
    monkeypatch.setattr(supabase_client, "get_client", lambda: fake_client)
    return fake_client


def test_sign_in_reads_role_from_admin_client(monkeypatch):
    _mock_auth_client(monkeypatch)

    monkeypatch.setattr(
        supabase_client,
        "get_admin_client",
        lambda: FakeQuery([{"rol": "admin"}]),
    )

    result = supabase_client.sign_in("ana@empresa.com", "clave-correcta")

    assert result["success"] is True
    assert result["rol"] == "admin"


def test_sign_in_defaults_to_usuario_when_no_profile_row(monkeypatch):
    _mock_auth_client(monkeypatch)

    monkeypatch.setattr(
        supabase_client,
        "get_admin_client",
        lambda: FakeQuery([]),  # sin fila en profiles
    )

    result = supabase_client.sign_in("ana@empresa.com", "clave-correcta")

    assert result["success"] is True
    assert result["rol"] == "usuario"


def test_sign_in_defaults_to_usuario_when_profile_query_fails(monkeypatch):
    _mock_auth_client(monkeypatch)

    monkeypatch.setattr(
        supabase_client,
        "get_admin_client",
        lambda: FakeFailingQuery([]),
    )

    result = supabase_client.sign_in("ana@empresa.com", "clave-correcta")

    # El login sigue siendo exitoso (la autenticación no depende del rol);
    # solo se degrada al rol con menos privilegios.
    assert result["success"] is True
    assert result["rol"] == "usuario"


def test_get_admin_client_requires_service_role_key(monkeypatch):
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")

    with pytest.raises(RuntimeError, match="SUPABASE_SERVICE_ROLE_KEY"):
        supabase_client.get_admin_client()
