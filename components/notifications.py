"""
Construcción de notificaciones tipo "toast" (mini ventanas de aviso que
aparecen en la esquina superior derecha y se cierran solas o con un
botón ✕).

Los callbacks NO crean toasts directamente: el flujo es

    callback existente -> mensaje inline (success/warning/error-message)
        -> callback "espejo" en callbacks/notifications.py
        -> dcc.Store("toast-inbox") -> make_toast() -> #toast-container

Así ningún callback existente tuvo que modificar su firma ni sus Outputs.
"""

import uuid

from dash import html


# Texto de cada tipo de toast. Los tipos mapean a las clases CSS
# `.toast-success` / `.toast-warning` / `.toast-error` (ver style.css).
TOAST_ICONS = {
    "success": "✓",
    "warning": "⚠️",
    "error": "❌",
}

TOAST_TYPES = tuple(TOAST_ICONS.keys())


def make_toast(text: str, toast_type: str = "success") -> html.Div:
    """
    Crea un toast individual: mensaje + botón de cierre manual.

    `toast_type` debe ser "success", "warning" o "error"; cualquier otro
    valor se degrada a "success" (el menos alarmante) en vez de romper.
    """

    if toast_type not in TOAST_ICONS:
        toast_type = "success"

    toast_id = uuid.uuid4().hex

    return html.Div(
        id={"type": "toast", "index": toast_id},
        className=f"toast toast-{toast_type}",
        children=[
            html.Span(
                TOAST_ICONS[toast_type],
                className="toast-icon",
            ),
            html.Span(
                text,
                className="toast-text",
            ),
            html.Button(
                "✕",
                id={"type": "toast-close", "index": toast_id},
                className="toast-close",
                n_clicks=0,
            ),
        ],
    )
