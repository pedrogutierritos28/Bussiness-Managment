"""
Pruebas de integración de los callbacks de app.py.

`dash.testing` (el framework "oficial" de Dash para pruebas de UI) requiere
Selenium + un navegador headless real, lo cual no está disponible en todos
los entornos de CI/ejecución. En su lugar, estas pruebas invocan
directamente las funciones de callback de app.py con datos reales
(un Excel generado en memoria, codificado en base64 tal como lo entrega
dcc.Upload desde el navegador), ejercitando el flujo completo:

    subir archivo -> analizar -> generar gráfica -> exportar

Esto cubre la lógica real de los callbacks (antes solo se probaban los
`services/`, dejando sin cobertura ~50% del código del proyecto). Si en el
futuro se agrega Selenium/chromedriver al entorno, estas pruebas pueden
complementarse (no reemplazarse) con pruebas de `dash.testing` que además
verifiquen renderizado real en el navegador.
"""

import base64
import io

import pandas as pd
import pytest
from dash.exceptions import PreventUpdate
from flask import session
from werkzeug.exceptions import HTTPException

import app as appmod


@pytest.fixture(autouse=True)
def authenticated_request():
    """
    Los callbacks protegidos llaman a `require_session()`, que lee
    `flask.session` y necesita un contexto de petición Flask activo (si
    no, lanza `RuntimeError: Working outside of request context`).

    Este fixture simula, para cada test, una petición YA autenticada
    (como la que deja un login exitoso vía Supabase), para que las
    pruebas de comportamiento de negocio no tengan que lidiar con el
    detalle de la sesión. Las pruebas de seguridad más abajo abren su
    propio contexto SIN marcar `authenticated`, precisamente para
    verificar el caso contrario.
    """

    ctx = appmod.app.server.test_request_context()
    ctx.push()
    session["authenticated"] = True
    session["user_email"] = "test@example.com"
    session["user_id"] = "test-user-id"
    yield
    ctx.pop()


def _make_upload_contents(dataframe: pd.DataFrame) -> str:
    """
    Simula el string `contents` que dcc.Upload entrega al callback:
    "data:<mime>;base64,<contenido codificado>".
    """

    buffer = io.BytesIO()
    dataframe.to_excel(buffer, index=False)
    encoded = base64.b64encode(buffer.getvalue()).decode()

    return f"data:application/vnd.openxmlformats;base64,{encoded}"


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        "Ventas": [100, 200, 300, 400, 500],
        "Region": ["Norte", "Sur", "Norte", "Sur", "Norte"],
        "Fecha": pd.date_range("2024-01-01", periods=5, freq="D"),
    })


# Índices del tuple devuelto por `process_excel` (equivalente a
# `_UploadState.as_outputs`). Se referencian por nombre para que un cambio
# en el orden de los Output no rompa silenciosamente las aserciones.
# Orden: status, info, preview, columnas, column_options, secondary_options,
#        excel_data, analysis, + 5 estilos de sección.
EXCEL_DATA = 6
ANALYSIS = 7
COLUMN_OPTIONS = 4


# ================================================================
# CALLBACK 1 · process_excel
# ================================================================

def test_process_excel_no_contents_returns_empty_state():
    result = appmod.process_excel(None, None)

    assert result[0] == ""
    assert result[EXCEL_DATA] is None
    assert result[ANALYSIS] is None


def test_process_excel_valid_file_populates_stores(sample_dataframe):
    contents = _make_upload_contents(sample_dataframe)

    result = appmod.process_excel(contents, "ventas.xlsx")

    dataframe_json = result[EXCEL_DATA]
    analysis = result[ANALYSIS]

    assert dataframe_json is not None
    assert analysis is not None
    assert analysis["rows"] == 5
    assert analysis["columns"] == 3

    column_options = result[COLUMN_OPTIONS]
    assert {"label": "Ventas", "value": "Ventas"} in column_options


def test_process_excel_rejects_invalid_extension(sample_dataframe):
    contents = _make_upload_contents(sample_dataframe)

    result = appmod.process_excel(contents, "reporte.txt")

    assert result[EXCEL_DATA] is None
    assert result[ANALYSIS] is None
    assert "Formato no soportado" in str(result[0])


def test_process_excel_rejects_oversized_file(sample_dataframe, monkeypatch):
    contents = _make_upload_contents(sample_dataframe)

    # La constante se lee dentro de callbacks/upload.py (tras la
    # reestructuración de app.py), así que el parche apunta ahí.
    monkeypatch.setattr("callbacks.upload.MAX_FILE_SIZE_BYTES", 10)

    result = appmod.process_excel(contents, "ventas.xlsx")

    assert result[EXCEL_DATA] is None
    assert "límite" in str(result[0])


def test_process_excel_warns_on_empty_dataframe():
    empty_df = pd.DataFrame(columns=["A", "B"])
    contents = _make_upload_contents(empty_df)

    result = appmod.process_excel(contents, "vacio.xlsx")

    assert result[EXCEL_DATA] is None
    assert "no contiene filas de datos" in str(result[0])


def test_process_excel_deduplicates_columns():
    dataframe = pd.DataFrame([[1, 2, 3]], columns=["Ventas", "Ventas", "Costo"])
    contents = _make_upload_contents(dataframe)

    result = appmod.process_excel(contents, "dup.xlsx")

    analysis = result[ANALYSIS]
    names = [column["name"] for column in analysis["column_info"]]

    assert len(names) == len(set(names))


# ================================================================
# CALLBACK 3 · generate_chart
# ================================================================

def test_generate_chart_end_to_end(sample_dataframe):
    contents = _make_upload_contents(sample_dataframe)
    upload_result = appmod.process_excel(contents, "ventas.xlsx")
    dataframe_json, analysis = upload_result[EXCEL_DATA], upload_result[ANALYSIS]

    figure, message, store_values, placeholder_style, chart_style = appmod.generate_chart(
        1, "Ventas", "bar", None, None, 25,
        dataframe_json, analysis
    )

    assert store_values is not None
    assert "success-message" in str(getattr(message, "className", ""))
    # Al generarse con éxito, el placeholder se oculta y la gráfica se muestra
    assert placeholder_style.get("display") == "none"
    assert chart_style.get("display") != "none"


def test_generate_chart_without_file_shows_warning():
    figure, message, store_values, placeholder_style, chart_style = appmod.generate_chart(
        1, "Ventas", "bar", None, None, 25,
        None, None
    )

    assert store_values is None
    assert "cargar un archivo" in str(message)
    # Sin gráfica generada, el placeholder debe seguir visible
    assert placeholder_style.get("display") != "none"
    assert chart_style.get("display") == "none"


def test_generate_chart_line_over_date_restores_datetime(sample_dataframe):
    contents = _make_upload_contents(sample_dataframe)
    upload_result = appmod.process_excel(contents, "ventas.xlsx")
    dataframe_json, analysis = upload_result[EXCEL_DATA], upload_result[ANALYSIS]

    figure, message, store_values, placeholder_style, chart_style = appmod.generate_chart(
        1, "Fecha", "line", None, "D", 25,
        dataframe_json, analysis
    )

    assert store_values is not None


# ================================================================
# CALLBACK 4/5/6 · exportaciones
# ================================================================

def test_export_csv_end_to_end(sample_dataframe):
    contents = _make_upload_contents(sample_dataframe)
    upload_result = appmod.process_excel(contents, "ventas.xlsx")
    dataframe_json = upload_result[EXCEL_DATA]
    analysis = upload_result[ANALYSIS]

    download, export_message = appmod.export_csv(1, dataframe_json, analysis)

    assert download is not None
    assert download["filename"] == "datos.csv"
    assert export_message == ""


def test_export_csv_without_file_shows_warning():
    download, export_message = appmod.export_csv(1, None, None)

    assert download is None
    assert "cargar un archivo" in str(export_message)


def test_export_csv_preserves_date_values(sample_dataframe):
    # Regresión de bug: el CSV exportado entregaba las fechas como texto
    # deserializado (p.ej. "Wed, 01 Jan 2024 00:00:00 GMT") porque read_json
    # las devolvía como cadenas. Debe producir una fecha con el formato
    # estándar pandas (ISO), no el timestamp textual que genera read_json.
    contents = _make_upload_contents(sample_dataframe)
    upload_result = appmod.process_excel(contents, "ventas.xlsx")
    dataframe_json = upload_result[EXCEL_DATA]
    analysis = upload_result[ANALYSIS]

    download, _ = appmod.export_csv(1, dataframe_json, analysis)

    csv_text = download["content"]

    assert "2024-01-01" in csv_text
    assert "GMT" not in csv_text


def test_export_report_end_to_end(sample_dataframe):
    contents = _make_upload_contents(sample_dataframe)
    upload_result = appmod.process_excel(contents, "ventas.xlsx")
    analysis = upload_result[ANALYSIS]

    download, export_message = appmod.export_report(1, analysis)

    assert download is not None
    assert download["filename"] == "reporte_calidad.csv"
    assert export_message == ""


def test_export_png_failure_does_not_leak_technical_details():
    # Sin kaleido instalado (u otra falla de generación), el mensaje
    # visible para el usuario NO debe mencionar librerías internas.
    download, export_message = appmod.export_png(
        1, {"data": [], "layout": {}}
    )

    message_text = str(export_message)

    assert download is None
    assert "kaleido" not in message_text.lower()
    assert "Error al generar la imagen PNG" in message_text


# ================================================================
# ANÁLISIS DE DISEÑO · secciones ocultas hasta cargar un archivo
# (antes: file-info/data-preview/columns-section/chart-builder-section/
# chart-result-section se veían como tarjetas blancas vacías, y el
# constructor de gráficas era interactuable sin datos)
# ================================================================

SECTION_STYLE_INDEXES = {
    "file-info": 8,
    "data-preview": 9,
    "columns-section": 10,
    "chart-builder-section": 11,
    "chart-result-section": 12,
}


def test_sections_hidden_when_no_file_uploaded():
    result = appmod.process_excel(None, None)

    for name, index in SECTION_STYLE_INDEXES.items():
        assert result[index].get("display") == "none", (
            f"la sección '{name}' debería estar oculta sin archivo"
        )


def test_sections_shown_after_valid_upload(sample_dataframe):
    contents = _make_upload_contents(sample_dataframe)
    result = appmod.process_excel(contents, "ventas.xlsx")

    for name, index in SECTION_STYLE_INDEXES.items():
        assert result[index].get("display") != "none", (
            f"la sección '{name}' debería mostrarse tras cargar un archivo"
        )


def test_sections_hidden_on_invalid_extension(sample_dataframe):
    contents = _make_upload_contents(sample_dataframe)
    result = appmod.process_excel(contents, "reporte.txt")

    for name, index in SECTION_STYLE_INDEXES.items():
        assert result[index].get("display") == "none", (
            f"la sección '{name}' debería seguir oculta en un error de "
            "validación"
        )


# ================================================================
# ANÁLISIS DE DISEÑO · placeholder de gráfica vs. gráfica real
# (antes: se mostraba un dcc.Graph vacío con ejes en blanco antes de
# generar cualquier gráfica)
# ================================================================

def test_chart_placeholder_visible_before_first_generation():
    _, _, _, placeholder_style, chart_style = appmod.generate_chart(
        1, None, None, None, None, 25, None, None
    )

    assert placeholder_style.get("display") != "none"
    assert chart_style.get("display") == "none"


def test_chart_placeholder_hidden_after_successful_generation(sample_dataframe):
    contents = _make_upload_contents(sample_dataframe)
    upload_result = appmod.process_excel(contents, "ventas.xlsx")
    dataframe_json, analysis = upload_result[EXCEL_DATA], upload_result[ANALYSIS]

    _, _, store_values, placeholder_style, chart_style = appmod.generate_chart(
        1, "Ventas", "histogram", None, None, 25,
        dataframe_json, analysis
    )

    assert store_values is not None
    assert placeholder_style.get("display") == "none"
    assert chart_style.get("display") != "none"


# ================================================================
# SEGURIDAD · los callbacks protegidos deben rechazar peticiones sin
# sesión autenticada (ver require_session() en app.py). Antes de este
# fix, cualquiera podía invocar estos callbacks directamente contra el
# servidor (comprobado con una petición HTTP manual a
# /_dash-update-component) sin pasar nunca por la pantalla de login.
# ================================================================

def _call_without_session(func, *args, **kwargs):
    """
    Ejecuta `func` dentro de un contexto de petición Flask SIN sesión
    autenticada: simula una petición directa al servidor que se salta
    el login (p. ej. vía curl/Postman contra /_dash-update-component).
    """

    ctx = appmod.app.server.test_request_context()
    ctx.push()
    try:
        return func(*args, **kwargs)
    finally:
        ctx.pop()


@pytest.mark.parametrize(
    "callback_name, args",
    [
        ("process_excel", (None, None)),
        ("update_chart_types", (None, None)),
        ("generate_chart", (1, None, None, None, None, 25, None, None)),
        ("export_csv", (1, None, None)),
        ("export_png", (1, None)),
        ("export_report", (1, None)),
    ],
)
def test_protected_callbacks_reject_unauthenticated_requests(callback_name, args):
    func = getattr(appmod, callback_name)

    with pytest.raises(HTTPException) as exc_info:
        _call_without_session(func, *args)

    assert exc_info.value.code == 401


def test_login_creates_authenticated_session(monkeypatch):
    monkeypatch.setattr(
        appmod.supabase_client,
        "sign_in",
        lambda email, password: {
            "success": True,
            "user": {"id": "abc123", "email": email},
            "rol": "admin",
            "error": None,
        },
    )

    ctx = appmod.app.server.test_request_context()
    ctx.push()
    try:
        appmod.authenticate(1, "user@empresa.com", "clave-correcta")
        assert session.get("authenticated") is True
        assert session.get("user_email") == "user@empresa.com"
        assert session.get("role") == "admin"
    finally:
        ctx.pop()


def test_login_defaults_to_usuario_role_when_missing(monkeypatch):
    # Si sign_in() no trae la clave "rol" por alguna razón, el login no
    # debe romperse: se asume "usuario", el rol con menos privilegios.
    monkeypatch.setattr(
        appmod.supabase_client,
        "sign_in",
        lambda email, password: {
            "success": True,
            "user": {"id": "abc123", "email": email},
            "error": None,
        },
    )

    ctx = appmod.app.server.test_request_context()
    ctx.push()
    try:
        appmod.authenticate(1, "user@empresa.com", "clave-correcta")
        assert session.get("role") == "usuario"
    finally:
        ctx.pop()


def test_failed_login_does_not_create_session(monkeypatch):
    monkeypatch.setattr(
        appmod.supabase_client,
        "sign_in",
        lambda email, password: {
            "success": False,
            "user": None,
            "error": "Invalid login credentials",
        },
    )

    ctx = appmod.app.server.test_request_context()
    ctx.push()
    try:
        card = appmod.authenticate(1, "user@empresa.com", "clave-mala")
        assert session.get("authenticated") is None
        assert "Credenciales incorrectas" in str(card)
    finally:
        ctx.pop()


def test_logout_clears_session():
    ctx = appmod.app.server.test_request_context()
    ctx.push()
    try:
        session["authenticated"] = True
        session["user_email"] = "user@empresa.com"

        appmod.logout(1)

        assert session.get("authenticated") is None
        assert session.get("user_email") is None
    finally:
        ctx.pop()


def test_logout_ignores_phantom_trigger_on_mount():
    """
    Regresión: al insertarse dinámicamente el botón "Cerrar sesión"
    (justo después de un login exitoso, cuando se reemplaza el layout
    de login por el del analizador), Dash puede disparar este callback
    una vez solo por el montaje del componente, con n_clicks en su
    valor inicial (0) -- prevent_initial_call NO cubre este caso porque
    solo aplica a la carga inicial real de la página, no a componentes
    insertados después por otro callback.

    Sin el guard `if not n_clicks: raise PreventUpdate`, esto cerraba la
    sesión recién creada medio segundo después de cada login exitoso.
    """

    ctx = appmod.app.server.test_request_context()
    ctx.push()
    try:
        session["authenticated"] = True
        session["user_email"] = "user@empresa.com"

        with pytest.raises(PreventUpdate):
            appmod.logout(0)

        # La sesión debe seguir intacta: el disparo fantasma no debe
        # alcanzar a ejecutar session.clear().
        assert session.get("authenticated") is True
        assert session.get("user_email") == "user@empresa.com"
    finally:
        ctx.pop()


def test_require_role_rejects_user_role_for_admin_only():
    # Un usuario con rol "usuario" no debe poder pasar una guarda que
    # solo admite "admin"/"superadmin": 403 (autenticado pero no autorizado).
    session["role"] = "usuario"

    with pytest.raises(HTTPException) as exc_info:
        appmod.require_role("admin", "superadmin")

    assert exc_info.value.code == 403


def test_require_role_allows_admin():
    session["role"] = "admin"

    # No debe lanzar nada.
    appmod.require_role("admin", "superadmin")


def test_require_role_requires_session():
    ctx = appmod.app.server.test_request_context()
    ctx.push()
    try:
        with pytest.raises(HTTPException) as exc_info:
            appmod.require_role("admin")

        assert exc_info.value.code == 401
    finally:
        ctx.pop()


# ================================================================
# NOTIFICACIONES TOAST
# ================================================================

def test_toast_payload_maps_inline_message_classes():
    from dash import html

    from callbacks.notifications import _toast_payload_from_message

    cases = {
        "success-message": "success",
        "warning-message": "warning",
        "error-message": "error",
    }

    for class_name, expected_type in cases.items():
        payload = _toast_payload_from_message(
            html.Div("Algo pasó", className=class_name)
        )

        assert payload is not None
        assert payload["type"] == expected_type
        assert "Algo pasó" in payload["text"]


def test_toast_payload_ignores_empty_or_plain_messages():
    from dash import html

    from callbacks.notifications import _toast_payload_from_message

    assert _toast_payload_from_message(None) is None
    assert _toast_payload_from_message("") is None
    assert _toast_payload_from_message("texto suelto") is None
    # Mensaje sin clase reconocida: no se notifica
    assert _toast_payload_from_message(html.Div("hola")) is None


def test_push_toast_appends_and_caps():
    from dash.exceptions import PreventUpdate

    import callbacks.notifications as notif

    with pytest.raises(PreventUpdate):
        notif.push_toast(None, [])

    children = notif.push_toast({"text": "Primero", "type": "success"}, [])
    assert len(children) == 1

    children = notif.push_toast(
        {"text": "Segundo", "type": "warning"}, children
    )
    assert len(children) == 2

    # Tope de toasts visibles
    for i in range(10):
        children = notif.push_toast(
            {"text": f"t{i}", "type": "success"}, children
        )

    assert len(children) == notif.MAX_VISIBLE_TOASTS


def test_logout_returns_session_closed_toast():
    ctx = appmod.app.server.test_request_context()
    ctx.push()
    try:
        session["authenticated"] = True

        layout, toast = appmod.logout(1)

        assert toast["type"] == "success"
        assert "Sesión cerrada" in toast["text"]
        assert session.get("authenticated") is None
    finally:
        ctx.pop()


def test_authenticate_ignores_phantom_trigger_on_mount():
    """
    Mismo caso que arriba, pero para el botón de login: se vuelve a
    montar dinámicamente después de un logout (login_layout() se
    reinserta como Output de `logout`), así que también es vulnerable
    al disparo fantasma de Dash.
    """

    ctx = appmod.app.server.test_request_context()
    ctx.push()
    try:
        with pytest.raises(PreventUpdate):
            appmod.authenticate(0, None, None)
    finally:
        ctx.pop()
