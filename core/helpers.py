"""
Helpers compartidos por los callbacks: mensajes de error seguros para la
UI y restauración de tipos de columnas tras deserializar DataFrames.
"""

from dash import html
import pandas as pd

from config import logger


def user_facing_error(prefix: str, error: Exception, technical_hint: str | None = None) -> "html.Div":
    """
    Registra el detalle técnico del error en el log del servidor y
    devuelve un mensaje genérico y amigable para mostrar en la UI.

    Esto evita exponer rutas de archivos, tipos internos, nombres de
    librerías o trazas de pandas/Python directamente al usuario final.

    `technical_hint` es información solo para el equipo técnico (ej. qué
    dependencia revisar): se registra en el log pero JAMÁS se muestra
    en pantalla, ya que el usuario de negocio no puede actuar sobre ella
    y solo genera confusión.
    """

    log_message = prefix if not technical_hint else f"{prefix} ({technical_hint})"
    logger.exception(log_message)

    return html.Div(
        f"❌ {prefix}. Verifica el archivo o inténtalo de nuevo. "
        "Si el problema persiste, contacta al equipo técnico.",
        className="error-message"
    )


def restore_column_types(dataframe: pd.DataFrame, analysis: dict | None) -> pd.DataFrame:
    """
    Reconstruye los tipos semánticos que ``pd.read_json(orient="split")``
    pierde al deserializar desde el ``dcc.Store``.

    En concreto, las columnas de fecha se guardan como texto en el JSON y
    ``read_json`` las devuelve como cadenas; aquí se reconvierten a
    ``datetime`` usando la información de tipos del análisis. Sin este
    paso, la generación de gráficas temporales fallaría y las exportaciones
    (CSV/reporte) entregarían las fechas en su forma textual en vez del
    valor de fecha real que el usuario ve en pantalla.

    Devuelve el mismo DataFrame modificado (no una copia).
    """

    if not analysis:
        return dataframe

    for column in analysis.get("column_info", []):
        name = column["name"]
        if column["type"] == "date" and name in dataframe.columns:
            dataframe[name] = pd.to_datetime(
                dataframe[name],
                format="mixed",
                errors="coerce",
            )

    return dataframe
