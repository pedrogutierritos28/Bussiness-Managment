"""
Callback de generación de gráficas: reconstruye el DataFrame desde el
dcc.Store, restaura tipos semánticos (fechas) y delega la generación a
services/chart_generator.
"""

import io

import pandas as pd
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

from app_instance import app, chart_generator
from core.helpers import restore_column_types, user_facing_error
from core.security import require_session


# ============================================================
# CALLBACK 3
# GENERAR GRÁFICA
# ============================================================

@app.callback(
    Output(
        "chart-output",
        "figure"
    ),

    Output(
        "chart-message",
        "children"
    ),

    Output(
        "current-figure-store",
        "data"
    ),

    Output(
        "chart-placeholder",
        "style"
    ),

    Output(
        "chart-output",
        "style"
    ),

    Input(
        "generate-chart",
        "n_clicks"
    ),

    State(
        "column-selector",
        "value"
    ),

    State(
        "chart-type-selector",
        "value"
    ),

    State(
        "secondary-column-selector",
        "value"
    ),

    State(
        "period-selector",
        "value"
    ),

    State(
        "nbins-slider",
        "value"
    ),

    State(
        "excel-data-store",
        "data"
    ),

    State(
        "analysis-store",
        "data"
    ),

    prevent_initial_call=True
)
def generate_chart(
    n_clicks,
    selected_column,
    selected_chart,
    secondary_column,
    period,
    nbins,
    dataframe_json,
    analysis
):

    require_session()

    # Guard contra el disparo fantasma de Dash al montar dinámicamente
    # el botón "Generar gráfica" dentro del layout del analizador.
    if not n_clicks:
        raise PreventUpdate

    # El placeholder ("Aquí aparecerá tu gráfica...") y la gráfica real
    # nunca se muestran a la vez: si esta ejecución no produce una
    # gráfica válida, dejamos visible el placeholder y el dcc.Graph
    # oculto, en vez de mostrar un gráfico vacío con ejes en blanco.
    show_placeholder = ({}, {"display": "none"})
    show_chart = ({"display": "none"}, {"width": "100%", "height": "600px"})

    def warning(text):
        return html.Div(text, className="warning-message")

    # ========================================================
    # VALIDACIONES
    # ========================================================

    if dataframe_json is None:

        return (
            {},
            warning("⚠️ Primero debes cargar un archivo Excel."),
            None,
            *show_placeholder
        )

    if selected_column is None:

        return (
            {},
            warning("⚠️ Selecciona una columna."),
            None,
            *show_placeholder
        )

    if selected_chart is None:

        return (
            {},
            warning("⚠️ Selecciona un tipo de gráfica."),
            None,
            *show_placeholder
        )

    try:

        # ====================================================
        # RECONSTRUIR DATAFRAME
        # ====================================================

        dataframe = pd.read_json(
            io.StringIO(dataframe_json),
            orient="split"
        )

        # ====================================================
        # RESTAURAR TIPOS SEMÁNTICOS (fechas perdidas por read_json)
        # ====================================================
        # pd.read_json devuelve las columnas de fecha como texto, por lo
        # que se reconstruyen a datetime usando la información del análisis.

        restore_column_types(dataframe, analysis)

        # ====================================================
        # GENERAR GRÁFICA
        # ====================================================

        figure = chart_generator.generate(
            dataframe=dataframe,
            column=selected_column,
            chart_type=selected_chart,
            secondary_column=secondary_column,
            period=period,
            nbins=nbins
        )

        # ====================================================
        # GUARDAR FIGURA PARA EXPORTACIÓN
        # ====================================================

        store_values = figure.to_plotly_json()

        # ====================================================
        # MENSAJE
        # ====================================================

        message = html.Div(
            "✓ Gráfica generada correctamente.",
            className="success-message"
        )

        return (
            figure,
            message,
            store_values,
            *show_chart
        )

    except Exception as error:

        return (
            {},
            user_facing_error(
                f"Error al generar la gráfica de '{selected_column}'",
                error
            ),
            None,
            *show_placeholder
        )
