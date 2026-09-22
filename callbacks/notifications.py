"""
Callbacks que convierten los mensajes inline en notificaciones toast.

DISEÑO — "callbacks espejo": en lugar de agregar un Output de toast a cada
callback existente (lo que habría obligado a cambiar sus firmas y rompería
los tests que desempaquetan sus tuplas de retorno), aquí se OBSERVAN los
mensajes que ya despliega la UI:

    - "file-status"    (carga del Excel)
    - "chart-message"  (generación de gráficas)
    - "export-message" (descargas CSV/PNG/reporte)

Cuando cualquiera de ellos recibe un mensaje con clase CSS
success/warning/error-message, este módulo lo replica como un toast.
El login fallido NO se replica (decisión de producto: su mensaje rojo
junto al formulario basta, sin duplicar avisos); el logout sí emite su
propio toast escribiendo directo en "toast-inbox".
"""

from dash import MATCH, Input, Output, State
from dash.exceptions import PreventUpdate

from app_instance import app
from components.notifications import make_toast


# Mapeo: clase CSS del mensaje inline -> tipo de toast.
MESSAGE_CLASS_TO_TOAST = {
    "success-message": "success",
    "warning-message": "warning",
    "error-message": "error",
}

# Máximo de toasts visibles en pantalla: al llegar al límite se descartan
# los más antiguos para no empapelar la esquina de la pantalla.
MAX_VISIBLE_TOASTS = 6


def _collect_text(node) -> str:
    """Extrae todo el texto de un árbol de componentes Dash."""

    if node is None:
        return ""

    if isinstance(node, str):
        return node

    children = getattr(node, "children", None)

    if children is None:
        return ""

    if isinstance(children, str):
        return children

    if isinstance(children, (list, tuple)):
        return " ".join(
            part for part in (_collect_text(child) for child in children)
            if part
        )

    return _collect_text(children)


def _toast_payload_from_message(children):
    """
    Traduce el `children` de un contenedor de mensajes inline a
    {"text": ..., "type": ...} para el buzón de toasts.

    Devuelve None cuando no hay nada que notificar (contenedor vacío,
    texto vacío o mensaje sin clase reconocida).
    """

    if not children or isinstance(children, str):

        # Un string suelto o vacío no es un mensaje con clase; ignorarlo.
        return None

    class_name = getattr(children, "className", "") or ""

    toast_type = next(
        (
            toast_type
            for class_token, toast_type in MESSAGE_CLASS_TO_TOAST.items()
            if class_token in class_name.split()
        ),
        None,
    )

    if toast_type is None:
        return None

    text = _collect_text(children).strip()

    if not text:
        return None

    return {"text": text, "type": toast_type}


def _register_mirror(target_id: str) -> None:
    """
    Registra el callback espejo de un contenedor de mensajes inline:
    cada vez que su `children` cambia a un mensaje success/warning/error,
    lo publica en el buzón de toasts.
    """

    @app.callback(
        Output("toast-inbox", "data", allow_duplicate=True),
        Input(target_id, "children"),
        prevent_initial_call=True,
    )
    def _mirror(children, _target=target_id):
        payload = _toast_payload_from_message(children)

        if payload is None:
            raise PreventUpdate

        return payload


for _message_container_id in ("file-status", "chart-message", "export-message"):
    _register_mirror(_message_container_id)


@app.callback(
    Output("toast-container", "children"),
    Input("toast-inbox", "data"),
    State("toast-container", "children"),
    prevent_initial_call=True,
)
def push_toast(payload, current_children):
    """
    ÚNICO escritor del contenedor de toasts: toma el último toast del
    buzón y lo agrega (los toasts anteriores se conservan mientras sigan
    visibles), con tope de MAX_VISIBLE_TOASTS.
    """

    if not payload:
        raise PreventUpdate

    children = list(current_children or [])
    children.append(
        make_toast(payload.get("text", ""), payload.get("type", "success"))
    )

    return children[-MAX_VISIBLE_TOASTS:]


# Cierre manual con el botón ✕: callback del lado del servidor con
# pattern-matching: cada toast tiene id {"type": "toast", "index": ...} y
# su botón {"type": "toast-close", "index": ...} con el MISMO index, así
# que este callback solo oculta el toast del botón presionado.
#
# (Primero se implementó como clientside callback en JavaScript embebido,
# pero los toasts se crean dinámicamente DESPUÉS de la carga de la página
# y ese mecanismo resultó poco fiable para componentes dinámicos: el
# botón no hacía nada. El roundtrip al servidor es imperceptible.)
@app.callback(
    Output({"type": "toast", "index": MATCH}, "style"),
    Input({"type": "toast-close", "index": MATCH}, "n_clicks"),
    prevent_initial_call=True,
)
def close_toast(n_clicks):

    # Guard contra la ejecución al aparecer el toast (n_clicks=0):
    # solo un clic real debe ocultarlo.
    if not n_clicks:
        raise PreventUpdate

    return {"display": "none"}
