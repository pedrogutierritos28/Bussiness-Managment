"""
Punto de entrada de la aplicación Dash.

Este archivo quedó deliberadamente pequeño; sus responsabilidades están
distribuidas así:

    config.py               <- constantes del entorno y logger
    app_instance.py         <- instancia Dash, SECRET_KEY, singletons
    core/security.py        <- is_authenticated, require_session, require_role
    core/helpers.py         <- user_facing_error, restore_column_types
    components/login.py     <- layout de la pantalla de login
    components/analyzer.py  <- layout del analizador (vista principal)
    callbacks/              <- todos los callbacks registrados con
                               @app.callback al importarse los módulos

Las re-exportaciones de abajo mantienen funcionando a quien hacía
`import app` y accedía a `app.process_excel`, `app.authenticate`, etc.
(en particular, la suite de tests).
"""

from dash import dcc, html

from config import (  # noqa: F401
    ALLOWED_UPLOAD_EXTENSIONS,
    DEBUG_MODE,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    logger,
)
from app_instance import analyzer, app, chart_generator  # noqa: F401
from components.login import login_layout  # noqa: F401
from core.helpers import restore_column_types, user_facing_error  # noqa: F401
from core.security import is_authenticated, require_role, require_session  # noqa: F401
from services import supabase_client  # noqa: F401

# Importar el paquete `callbacks` registra todos los decoradores
# @app.callback (el registro ocurre al importar los módulos).
from callbacks import (  # noqa: F401
    auth,
    chart,
    chart_controls,
    exports,
    upload,
)
from callbacks.auth import authenticate, logout  # noqa: F401
from callbacks.chart import generate_chart  # noqa: F401
from callbacks.chart_controls import (  # noqa: F401
    update_advanced_controls,
    update_chart_types,
)
from callbacks.exports import export_csv, export_png, export_report  # noqa: F401
from callbacks.upload import process_excel  # noqa: F401
from components.analyzer import analyzer_layout  # noqa: F401


# ============================================================
# LAYOUT RAÍZ
# ============================================================
# El layout raíz es un contenedor neutro cuyo único hijo se sustituye por
# el callback de autenticación: arranca mostrando el login y, tras validar
# credenciales, intercambia su contenido por la vista del analizador.

app.layout = html.Div(
    [
        html.Div(id="app-container", children=login_layout()),

        # Buzón de notificaciones: los callbacks "espejo" (ver
        # callbacks/notifications.py) escriben aquí el toast a mostrar,
        # y un único callback lo materializa en #toast-container.
        dcc.Store(id="toast-inbox"),

        # Contenedor fijo de toasts (esquina superior derecha). Vive
        # FUERA de #app-container para seguir existiendo en el login y
        # no desaparecer con los cambios de pantalla.
        html.Div(id="toast-container", className="toast-container"),
    ]
)


if __name__ == "__main__":

    if DEBUG_MODE:
        logger.warning(
            "DASH_DEBUG=true: el debugger interactivo de Werkzeug está "
            "ACTIVO. No uses esta configuración en producción, ya que "
            "permite ejecución de código arbitrario desde el navegador."
        )

    app.run(
        debug=DEBUG_MODE
    )
