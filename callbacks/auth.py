"""
Callbacks de autenticación y navegación: login (crea la sesión de
servidor y guarda el rol) y logout (limpia la sesión).
"""

from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
from flask import session

from app_instance import app
from components.analyzer import analyzer_layout
from components.login import login_layout
from config import logger
from services import supabase_client


# ============================================================
# CALLBACK 7
# AUTENTICACIÓN Y NAVEGACIÓN (login -> analizador)
# ============================================================

@app.callback(
    Output("app-container", "children"),
    Input("login-button", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def authenticate(n_clicks, email, password):
    """
    Valida las credenciales contra Supabase Auth.

    Al autenticarse correctamente, crea la sesión de servidor (cookie
    firmada con SECRET_KEY) y sustituye el layout de login por el del
    analizador. En caso de error, devuelve el layout de login con un
    mensaje visible para el usuario, SIN revelar cuál campo falló ni el
    detalle técnico de Supabase (evita enumeración de usuarios y fugas
    de información interna).
    """

    # Mismo guard que en `logout`: el botón de login se vuelve a montar
    # dinámicamente después de un cierre de sesión (login_layout() se
    # reinserta como Output de `logout`), así que también es vulnerable
    # al disparo fantasma de Dash al insertarse un componente nuevo.
    if not n_clicks:
        raise PreventUpdate

    result = supabase_client.sign_in(email, password)

    if not result["success"]:
        # El detalle técnico (result["error"]) se registra en el log del
        # servidor únicamente; nunca se muestra al usuario.
        logger.info(
            "Intento de login fallido para %r: %s",
            email,
            result["error"],
        )

        card = login_layout()
        card.children[0].children.append(
            html.Div(
                "Credenciales incorrectas. Verifica tu correo y contraseña.",
                className="error-message",
            )
        )
        return card

    # Login válido: se crea la sesión de servidor. A partir de aquí,
    # is_authenticated() devuelve True para las peticiones que traigan
    # esta cookie, y los callbacks protegidos dejan de rechazarlas.
    session["authenticated"] = True
    session["user_email"] = result["user"]["email"]
    session["user_id"] = result["user"]["id"]

    # El rol ya viene resuelto desde supabase_client.sign_in() (lee
    # public.profiles con el cliente admin). No se vuelve a consultar
    # aquí: hacerlo duplicaría la llamada de red en cada login y, si se
    # hiciera con el cliente de la anon key, dependería de políticas RLS
    # y de un cliente compartido entre sesiones concurrentes (ver
    # services/supabase_client.py).
    session["role"] = result.get("rol", "usuario")

    logger.info("Inicio de sesión exitoso para %s", result["user"]["email"])

    return analyzer_layout()


@app.callback(
    Output("app-container", "children", allow_duplicate=True),
    Output("toast-inbox", "data", allow_duplicate=True),
    Input("logout-button", "n_clicks"),
    prevent_initial_call=True,
)
def logout(n_clicks):
    """
    Cierra la sesión de servidor y regresa a la pantalla de login.

    Limpiar `flask.session` es lo que realmente importa: sin esto, la
    cookie seguiría siendo válida y los callbacks protegidos seguirían
    aceptando peticiones aunque la pantalla ya no muestre el analizador.
    """

    # GUARDA CONTRA EL "DISPARO FANTASMA" DE DASH: cuando este botón se
    # inserta dinámicamente (al reemplazar el login por el analizador),
    # Dash puede ejecutar este callback UNA VEZ solo por haberse montado
    # el componente, incluso con prevent_initial_call=True (esa bandera
    # solo cubre la carga inicial real de la página, no la inserción
    # posterior de un componente nuevo vía otro callback). Sin este
    # guard, cada login exitoso se deshacía solo medio segundo después.
    if not n_clicks:
        raise PreventUpdate

    user_email = session.get("user_email", "desconocido")
    session.clear()

    logger.info("Cierre de sesión para %s", user_email)

    # Además de regresar al login, se publica un toast de confirmación
    # (el buzón lo convierte en notificación visible). Alcance: es el
    # único toast de autenticación; el login fallido mantiene solo su
    # mensaje inline para no duplicar avisos.
    return login_layout(), {
        "text": "Sesión cerrada correctamente.",
        "type": "success",
    }
