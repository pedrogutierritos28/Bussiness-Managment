"""
Callbacks de exportación: descarga de datos en CSV, gráfica en PNG y
reporte de calidad en CSV.
"""

import io

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

from app_instance import app
from core.helpers import restore_column_types, user_facing_error
from core.security import require_session


# ============================================================
# CALLBACK 4
# DESCARGAR DATOS EN CSV
# ============================================================

@app.callback(
    Output("download-csv", "data"),
    Output("export-message", "children"),
    Input("export-csv", "n_clicks"),
    State("excel-data-store", "data"),
    State("analysis-store", "data"),
    prevent_initial_call=True
)
def export_csv(n_clicks, dataframe_json, analysis):

    require_session()

    if not n_clicks:
        raise PreventUpdate

    if dataframe_json is None:
        return None, html.Div(
            "⚠️ Primero debes cargar un archivo Excel.",
            className="warning-message"
        )

    try:

        dataframe = pd.read_json(
            io.StringIO(dataframe_json),
            orient="split"
        )

        # Reconstruir tipos (fechas) antes de exportar para que el CSV
        # entregue los mismos valores que se ven en pantalla.
        restore_column_types(dataframe, analysis)

        return dcc.send_data_frame(
            dataframe.to_csv,
            "datos.csv",
            index=False
        ), ""

    except Exception as error:

        return None, user_facing_error(
            "Error al exportar el CSV",
            error
        )


# ============================================================
# CALLBACK 5
# DESCARGAR GRÁFICA EN PNG
# ============================================================

@app.callback(
    Output("download-png", "data"),
    Output("export-message", "children", allow_duplicate=True),
    Input("export-png", "n_clicks"),
    State("current-figure-store", "data"),
    prevent_initial_call=True
)
def export_png(n_clicks, figure_data):

    require_session()

    if not n_clicks:
        raise PreventUpdate

    if figure_data is None:
        return None, html.Div(
            "⚠️ Primero debes generar una gráfica.",
            className="warning-message"
        )

    try:

        figure = go.Figure(figure_data)

        # figure.to_image() depende de "kaleido", que a su vez requiere
        # un binario headless de Chrome instalado en el entorno. Si no
        # está disponible, lanza una excepción que antes tumbaba el
        # callback sin ningún mensaje para el usuario.
        image_bytes = figure.to_image(
            format="png",
            width=1200,
            height=600,
            scale=2
        )

        return dcc.send_bytes(
            image_bytes,
            "grafica.png"
        ), ""

    except Exception as error:

        return None, user_facing_error(
            "Error al generar la imagen PNG",
            error,
            technical_hint=(
                "verificar que el paquete 'kaleido' y su binario "
                "headless de Chrome estén instalados en el servidor"
            )
        )


# ============================================================
# CALLBACK 6
# DESCARGAR REPORTE DE CALIDAD
# ============================================================

@app.callback(
    Output("download-report", "data"),
    Output("export-message", "children", allow_duplicate=True),
    Input("export-report", "n_clicks"),
    State("analysis-store", "data"),
    prevent_initial_call=True
)
def export_report(n_clicks, analysis):

    require_session()

    if not n_clicks:
        raise PreventUpdate

    if analysis is None:
        return None, html.Div(
            "⚠️ Primero debes cargar un archivo Excel.",
            className="warning-message"
        )

    try:

        quality = analysis.get("quality_summary", {})
        columns = analysis.get("column_info", [])

        rows = []

        for column in columns:
            rows.append(
                {
                    "Columna": column["name"],
                    "Tipo": column["type"],
                    "Vacíos": column["total_missing"],
                    "Únicos": column["unique"],
                    "Total": column["total"],
                    "Promedio": column.get("statistics", {}).get("mean", ""),
                    "Mínimo": column.get("statistics", {}).get("min", ""),
                    "Máximo": column.get("statistics", {}).get("max", ""),
                }
            )

        report_df = pd.DataFrame(rows)

        if report_df.empty:
            report_df = pd.DataFrame(
                [{"Columna": "", "Tipo": "", "Vacíos": "", "Únicos": "", "Total": "", "Promedio": "", "Mínimo": "", "Máximo": ""}]
            )

        extra = pd.DataFrame(
            [
                {
                    "Columna": "", "Tipo": "CALIDAD GLOBAL", "Vacíos": "",
                    "Únicos": "", "Total": "",
                    "Promedio": f"Completitud: {quality.get('completeness_score', '')}%",
                    "Mínimo": f"Duplicados: {quality.get('duplicate_rows', 0)}",
                    "Máximo": ""
                }
            ]
        )

        final_df = pd.concat([report_df, extra], ignore_index=True)

        return dcc.send_data_frame(
            final_df.to_csv,
            "reporte_calidad.csv",
            index=False
        ), ""

    except Exception as error:

        return None, user_facing_error(
            "Error al generar el reporte de calidad",
            error
        )
