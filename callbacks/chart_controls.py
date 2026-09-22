"""
Callbacks de los controles del generador de gráficas: lista de tipos de
gráfica compatibles con la columna seleccionada y visibilidad de los
controles avanzados (segunda columna, periodo, bins).
"""

from dash import Input, Output, State

from app_instance import app, chart_generator
from core.security import require_session


# ============================================================
# CALLBACK 2
# ACTUALIZAR TIPOS DE GRÁFICA
# ============================================================

@app.callback(
    Output(
        "chart-type-selector",
        "options"
    ),

    Input(
        "column-selector",
        "value"
    ),

    State(
        "analysis-store",
        "data"
    )
)
def update_chart_types(
    selected_column,
    analysis
):

    require_session()

    if (
        selected_column is None
        or analysis is None
    ):

        return []

    # ========================================================
    # BUSCAR COLUMNA
    # ========================================================

    column_type = None

    for column in analysis["column_info"]:

        if column["name"] == selected_column:

            column_type = column["type"]

            break

    if column_type is None:

        return []

    # ========================================================
    # OBTENER GRÁFICAS COMPATIBLES
    # ========================================================

    return chart_generator.get_available_charts(
        column_type
    )


# ============================================================
# CALLBACK 2b
# MOSTRAR/OCULTAR CONTROLES AVANZADOS SEGÚN EL TIPO DE GRÁFICA
# ============================================================

@app.callback(
    Output("advanced-controls", "style"),
    Output("secondary-column-group", "style"),
    Output("period-group", "style"),
    Output("nbins-group", "style"),

    Input("chart-type-selector", "value"),

    State("column-selector", "value"),

    State("analysis-store", "data")
)
def update_advanced_controls(chart_type, selected_column, analysis):

    hidden = {"display": "none"}
    shown = {}

    empty = (
        {"display": "none"},
        hidden,
        hidden,
        hidden
    )

    if chart_type is None:
        return empty

    # Determinar el tipo de la columna seleccionada
    column_type = None

    if selected_column and analysis:
        for column in analysis["column_info"]:
            if column["name"] == selected_column:
                column_type = column["type"]
                break

    # Dispersión: mostrar selector de segunda columna
    if chart_type == "scatter":
        return (
            shown,
            shown,
            hidden,
            hidden
        )

    # Línea sobre fecha: mostrar selector de periodo
    if chart_type == "line" and column_type == "date":
        return (
            shown,
            hidden,
            shown,
            hidden
        )

    # Histograma: mostrar control de bins
    if chart_type == "histogram":
        return (
            shown,
            hidden,
            hidden,
            shown
        )

    # Cualquier otro caso (bar, line sin fecha, pie, box): ocultar
    return empty
