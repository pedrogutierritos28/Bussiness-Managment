from typing import Any, cast
import base64
import io

import pandas as pd
import plotly.graph_objects as go

from dash import (
    Dash,
    dcc,
    html,
    dash_table,
    Input,
    Output,
    State,
)

from services.excel_analyzer import ExcelAnalyzer
from services.chart_generator import ChartGenerator


# ============================================================
# CONFIGURACIÓN
# ============================================================

app = Dash(
    __name__,
    title="CA Y LI Analyzer"
)

analyzer = ExcelAnalyzer()
chart_generator = ChartGenerator()


# ============================================================
# LAYOUT
# ============================================================

app.layout = html.Div(
    className="app-container",
    children=[

        # ====================================================
        # ENCABEZADO
        # ====================================================

        html.Header(
            className="header",
            children=[

                html.Div(
                    className="brand",
                    children=[

                        html.H1(
                            "CA Y LI Analyzer",
                            className="title"
                        ),

                        html.P(
                            "Análisis inteligente de archivos Excel",
                            className="subtitle"
                        )
                    ]
                )
            ]
        ),

        # ====================================================
        # CONTENIDO
        # ====================================================

        html.Main(
            className="main-content",
            children=[

                # ==================================================
                # CARGA DEL ARCHIVO
                # ==================================================

                html.Section(
                    className="upload-section",
                    children=[

                        html.H2(
                            "Importar archivo",
                            className="section-title"
                        ),

                        html.P(
                            "Selecciona un archivo Excel para comenzar.",
                            className="section-description"
                        ),

                        dcc.Upload(
                            id="upload-excel",

                            children=html.Div(
                                [

                                    html.Div(
                                        "📂",
                                        className="upload-icon"
                                    ),

                                    html.Div(
                                        "Arrastra tu archivo aquí"
                                    ),

                                    html.Div(
                                        "o haz clic para seleccionarlo",
                                        className="upload-secondary"
                                    ),

                                    html.Div(
                                        "Formatos compatibles: .xlsx, .xls",
                                        className="upload-format"
                                    )
                                ]
                            ),

                            className="upload-box",

                            multiple=False
                        ),

                        html.Div(
                            id="file-status",
                            className="file-status"
                        )
                    ]
                ),

                # ==================================================
                # INFORMACIÓN DEL ARCHIVO
                # ==================================================

                html.Section(
                    id="file-info",
                    className="file-info-section"
                ),

                # ==================================================
                # VISTA PREVIA
                # ==================================================

                html.Section(
                    id="data-preview",
                    className="preview-section"
                ),

                # ==================================================
                # COLUMNAS DETECTADAS
                # ==================================================

                html.Section(
                    id="columns-section",
                    className="columns-section"
                ),

                # ==================================================
                # GENERADOR DE GRÁFICAS
                # ==================================================

                html.Section(
                    id="chart-builder-section",
                    className="chart-builder-section",

                    children=[

                        html.H2(
                            "Crear gráfica",
                            className="section-title"
                        ),

                        html.P(
                            "Selecciona una columna y el tipo de gráfica.",
                            className="section-description"
                        ),

                        html.Div(
                            className="chart-controls",

                            children=[

                                # ----------------------------------
                                # COLUMNA
                                # ----------------------------------

                                html.Div(
                                    className="control-group",
                                    children=[

                                        html.Label(
                                            "Columna",
                                            className="control-label"
                                        ),

                                        dcc.Dropdown(
                                            id="column-selector",

                                            options=[],

                                            placeholder=(
                                                "Selecciona una columna..."
                                            ),

                                            clearable=False
                                        )
                                    ]
                                ),

                                # ----------------------------------
                                # TIPO DE GRÁFICA
                                # ----------------------------------

                                html.Div(
                                    className="control-group",
                                    children=[

                                        html.Label(
                                            "Tipo de gráfica",
                                            className="control-label"
                                        ),

                                        dcc.Dropdown(
                                            id="chart-type-selector",

                                            options=[],

                                            placeholder=(
                                                "Selecciona un tipo..."
                                            ),

                                            clearable=False
                                        )
                                    ]
                                ),

                                # ----------------------------------
                                # BOTÓN
                                # ----------------------------------

                                html.Button(
                                    "📊 Generar gráfica",

                                    id="generate-chart",

                                    className="generate-button",

                                    n_clicks=0
                                )
                            ]
                        ),

                        # ------------------------------------------
                        # AGRUPACIÓN OPCIONAL (resumir datos)
                        # ------------------------------------------

                        html.Div(
                            className="chart-controls aggregation-controls",

                            children=[

                                html.Div(
                                    className="control-group",
                                    children=[

                                        html.Label(
                                            "Resumir por",
                                            className="control-label"
                                        ),

                                        dcc.Dropdown(
                                            id="group-by-selector",

                                            options=[],

                                            placeholder=(
                                                "Agrupar por..."
                                            ),

                                            clearable=True
                                        )
                                    ]
                                ),

                                html.Div(
                                    className="control-group",
                                    children=[

                                        html.Label(
                                            "Función",
                                            className="control-label"
                                        ),

                                        dcc.Dropdown(
                                            id="agg-selector",

                                            options=[
                                                {
                                                    "value": "count",
                                                    "label": "🔢 Conteo"
                                                },
                                                {
                                                    "value": "sum",
                                                    "label": "➕ Suma"
                                                },
                                                {
                                                    "value": "mean",
                                                    "label": "📐 Promedio"
                                                },
                                                {
                                                    "value": "min",
                                                    "label": "⬇️ Mínimo"
                                                },
                                                {
                                                    "value": "max",
                                                    "label": "⬆️ Máximo"
                                                }
                                            ],

                                            value="sum",

                                            placeholder=(
                                                "Selecciona una función..."
                                            ),

                                            clearable=False
                                        )
                                    ]
                                ),

                                html.Div(
                                    className="control-note",
                                    children=
                                        "Agrupa una columna numérica por una "
                                        "categoría o fecha para resumirla."
                                )
                            ]
                        ),

                        # ------------------------------------------
                        # OPCIONES AVANZADAS (dispersión, periodo, bins)
                        # ------------------------------------------

                        html.Div(
                            className="chart-controls advanced-controls",

                            id="advanced-controls",

                            style={"display": "none"},

                            children=[

                                html.Div(
                                    className="control-group",
                                    id="secondary-column-group",
                                    children=[

                                        html.Label(
                                            "Segunda columna (X)",
                                            className="control-label"
                                        ),

                                        dcc.Dropdown(
                                            id="secondary-column-selector",

                                            options=[],

                                            placeholder=(
                                                "Columna para dispersión..."
                                            ),

                                            clearable=True
                                        )
                                    ]
                                ),

                                html.Div(
                                    className="control-group",
                                    id="period-group",
                                    children=[

                                        html.Label(
                                            "Periodo temporal",
                                            className="control-label"
                                        ),

                                        dcc.Dropdown(
                                            id="period-selector",

                                            options=[
                                                {
                                                    "value": "D",
                                                    "label": "📅 Diario"
                                                },
                                                {
                                                    "value": "W",
                                                    "label": "🗓️ Semanal"
                                                },
                                                {
                                                    "value": "M",
                                                    "label": "📆 Mensual"
                                                },
                                                {
                                                    "value": "Q",
                                                    "label": "📊 Trimestral"
                                                },
                                                {
                                                    "value": "Y",
                                                    "label": "🗃️ Anual"
                                                }
                                            ],

                                            placeholder=(
                                                "Automático..."
                                            ),

                                            clearable=True
                                        )
                                    ]
                                ),

                                html.Div(
                                    className="control-group",
                                    id="nbins-group",
                                    children=[

                                        html.Label(
                                            "Barras del histograma",
                                            className="control-label"
                                        ),

                                        dcc.Slider(
                                            id="nbins-slider",

                                            min=5,
                                            max=100,
                                            step=5,
                                            value=25,
                                            marks={
                                                10: "10",
                                                25: "25",
                                                50: "50",
                                                75: "75",
                                                100: "100"
                                            },

                                            tooltip={
                                                "placement": "bottom"
                                            }
                                        )
                                    ]
                                )
                            ]
                        ),

                        # ------------------------------------------
                        # MENSAJES
                        # ------------------------------------------

                        html.Div(
                            id="chart-message",
                            className="chart-message"
                        )
                    ]
                ),

                # ==================================================
                # RESULTADO
                # ==================================================

                html.Section(
                    id="chart-result-section",

                    className="chart-result-section",

                    children=[

                        html.H2(
                            "Resultado",
                            className="section-title"
                        ),

                        html.Div(
                            className="export-bar",

                            children=[

                                html.Button(
                                    "⬇️ Descargar CSV",

                                    id="export-csv",

                                    className="export-button",

                                    n_clicks=0
                                ),

                                html.Button(
                                    "🖼️ Descargar gráfica PNG",

                                    id="export-png",

                                    className="export-button",

                                    n_clicks=0
                                ),

                                html.Button(
                                    "📋 Descargar reporte calidad",

                                    id="export-report",

                                    className="export-button",

                                    n_clicks=0
                                ),

                                html.Div(
                                    id="export-message",
                                    className="chart-message"
                                )
                            ]
                        ),

                        dcc.Graph(
                            id="chart-output",

                            style={
                                "width": "100%",
                                "height": "600px"
                            },

                            config={
                                "displaylogo": False,
                                "toImageButtonOptions": {
                                    "format": "png",
                                    "filename": "grafica",
                                    "height": 600,
                                    "width": 1200,
                                    "scale": 2
                                }
                            }
                        )
                    ]
                ),

                # ==================================================
                # STORE
                # ==================================================

                dcc.Store(
                    id="excel-data-store"
                ),

                dcc.Store(
                    id="analysis-store"
                ),

                dcc.Store(
                    id="current-figure-store"
                ),

                # ==================================================
                # DESCARGAS
                # ==================================================

                dcc.Download(
                    id="download-csv"
                ),

                dcc.Download(
                    id="download-png"
                ),

                dcc.Download(
                    id="download-report"
                )
            ]
        )
    ]
)


# ============================================================
# CALLBACK 1
# CARGAR Y ANALIZAR EXCEL
# ============================================================

@app.callback(
    Output("file-status", "children"),
    Output("file-info", "children"),
    Output("data-preview", "children"),
    Output("columns-section", "children"),
    Output("column-selector", "options"),
    Output("group-by-selector", "options"),
    Output("secondary-column-selector", "options"),
    Output("excel-data-store", "data"),
    Output("analysis-store", "data"),

    Input(
        "upload-excel",
        "contents"
    ),

    State(
        "upload-excel",
        "filename"
    )
)
def process_excel(contents, filename):

    if contents is None:

        return (
            "",
            "",
            "",
            "",
            [],
            [],
            [],
            None,
            None
        )

    try:

        # ====================================================
        # DECODIFICAR
        # ====================================================

        content_type, content_string = contents.split(",")

        decoded = base64.b64decode(
            content_string
        )

        file_buffer = io.BytesIO(
            decoded
        )

        # ====================================================
        # LEER EXCEL
        # ====================================================

        dataframe = pd.read_excel(
            file_buffer
        )

        # ====================================================
        # ANALIZAR
        # ====================================================

        result = analyzer.analyze(
            dataframe
        )

        # ====================================================
        # CONVERTIR DATAFRAME A JSON
        # ====================================================

        dataframe_json = dataframe.to_json(
            orient="split",
            date_format="iso"
        )

        # ====================================================
        # MENSAJE DE ÉXITO
        # ====================================================

        status = html.Div(
            [

                html.Span(
                    "✓ ",
                    className="success-icon"
                ),

                html.Span(
                    f"{filename} cargado correctamente"
                )
            ],

            className="success-message"
        )

        # ====================================================
        # INFORMACIÓN
        # ====================================================

        info = html.Div(
            [

                html.Div(
                    [

                        html.Span(
                            "Archivo"
                        ),

                        html.Strong(
                            str(filename)
                        )

                    ],

                    className="info-card"
                ),

                html.Div(
                    [

                        html.Span(
                            "Registros"
                        ),

                        html.Strong(
                            f"{result['rows']:,}"
                        )

                    ],

                    className="info-card"
                ),

                html.Div(
                    [

                        html.Span(
                            "Columnas"
                        ),

                        html.Strong(
                            str(result["columns"])
                        )

                    ],

                    className="info-card"
                ),

                html.Div(
                    [

                        html.Span(
                            "Calidad de datos"
                        ),

                        html.Strong(
                            f"{result['quality_summary']['completeness_score']}%"
                        ),

                        html.Small(
                            f"{result['quality_summary']['duplicate_rows']} duplicados"
                        )

                    ],

                    className="info-card"
                )

            ],

            className="info-grid"
        )

        # ====================================================
        # VISTA PREVIA
        # ====================================================

        preview_data = cast(
            Any,
            dataframe
            .head(10)
            .to_dict("records")
        )

        preview_columns = cast(
            Any,
            [
                {
                    "name": str(column),
                    "id": str(column)
                }

                for column in dataframe.columns
            ]
        )

        preview = html.Div(
            [

                html.H2(
                    "Vista previa",
                    className="section-title"
                ),

                dash_table.DataTable(

                    data=preview_data,

                    columns=preview_columns,

                    page_size=10,

                    style_table={
                        "overflowX": "auto"
                    },

                    style_cell={
                        "padding": "12px",
                        "textAlign": "left"
                    },

                    style_header={
                        "fontWeight": "bold"
                    }
                )
            ]
        )

        # ====================================================
        # COLUMNAS DETECTADAS
        # ====================================================

        icons = {

            "numeric": "🔢",

            "date": "📅",

            "categorical": "🏷️",

            "boolean": "☑️",

            "text": "📝"
        }

        type_names = {

            "numeric": "Numérico",

            "date": "Fecha",

            "categorical": "Categórico",

            "boolean": "Booleano",

            "text": "Texto"
        }

        column_cards = []

        for column in result["column_info"]:

            column_type = column["type"]

            details = [
                html.Strong(
                    column["name"]
                ),

                html.Span(
                    type_names.get(
                        column_type,
                        column_type
                    ),

                    className="column-type"
                ),

                html.Small(
                    f"{column['unique']} valores únicos · "
                    f"{column['total_missing']} vacíos"
                )
            ]

            # ====================================================
            # ESTADÍSTICAS DESCRIPTIVAS (solo numéricas)
            # ====================================================

            statistics = column.get("statistics", {})

            if statistics:

                identifier_badge = ""

                if column.get("identifier"):
                    identifier_badge = " · 🔑 ID"

                details.append(
                    html.Small(
                        f"Promedio {statistics.get('mean', '—')} · "
                        f"Mín {statistics.get('min', '—')} · "
                        f"Máx {statistics.get('max', '—')}"
                        f"{identifier_badge}",

                        className="column-stats"
                    )
                )

            card = html.Div(
                [

                    html.Div(
                        icons.get(
                            column_type,
                            "📄"
                        ),

                        className="column-icon"
                    ),

                    html.Div(
                        details,

                        className="column-details"
                    )
                ],

                className="column-card"
            )

            column_cards.append(
                card
            )

        columns_view = html.Div(
            [

                html.H2(
                    "Columnas detectadas",
                    className="section-title"
                ),

                html.Div(
                    column_cards,

                    className="columns-grid"
                )
            ]
        )

        # ====================================================
        # OPCIONES DE COLUMNAS
        # ====================================================

        column_options = [

            {
                "label": str(column["name"]),
                "value": str(column["name"])
            }

            for column in result["column_info"]
        ]

        # ====================================================
        # COLUMNAS PARA AGRUPAR (categóricas, fechas, booleanas)
        # ====================================================

        group_by_types = {"categorical", "date", "boolean"}

        group_by_options = [

            {
                "label": str(column["name"]),
                "value": str(column["name"])
            }

            for column in result["column_info"]
            if column["type"] in group_by_types
        ]

        # ====================================================
        # COLUMNAS NUMÉRICAS (para dispersión / eje X)
        # ====================================================

        secondary_options = [

            {
                "label": str(column["name"]),
                "value": str(column["name"])
            }

            for column in result["column_info"]
            if column["type"] == "numeric"
        ]

        return (

            status,

            info,

            preview,

            columns_view,

            column_options,

            group_by_options,

            secondary_options,

            dataframe_json,

            result
        )

    except Exception as error:

        error_message = html.Div(
            [

                "❌ Error al procesar el archivo: ",

                str(error)

            ],

            className="error-message"
        )

        return (

            error_message,

            "",

            "",

            "",

            [],

            [],

            [],

            None,

            None
        )


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

    # Cualquier otro caso: ocultar todo
    return empty


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
        "group-by-selector",
        "value"
    ),

    State(
        "agg-selector",
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
    group_by,
    agg,
    secondary_column,
    period,
    nbins,
    dataframe_json,
    analysis
):

    # ========================================================
    # VALIDACIONES
    # ========================================================

    if dataframe_json is None:

        return (
            {},
            "⚠️ Primero debes cargar un archivo Excel.",
            None
        )

    if selected_column is None:

        return (
            {},
            "⚠️ Selecciona una columna.",
            None
        )

    if selected_chart is None:

        return (
            {},
            "⚠️ Selecciona un tipo de gráfica.",
            None
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

        if analysis:
            for column in analysis.get("column_info", []):
                name = column["name"]
                if column["type"] == "date" and name in dataframe.columns:
                    dataframe[name] = pd.to_datetime(
                        dataframe[name],
                        format="mixed",
                        errors="coerce"
                    )

        # ====================================================
        # GENERAR GRÁFICA
        # ====================================================

        figure = chart_generator.generate(
            dataframe=dataframe,
            column=selected_column,
            chart_type=selected_chart,
            group_by=group_by,
            agg=agg,
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
            store_values
        )

    except Exception as error:

        return (
            {},
            html.Div(
                f"❌ Error al generar la gráfica: {error}",
                className="error-message"
            ),
            None
        )


# ============================================================
# CALLBACK 4
# DESCARGAR DATOS EN CSV
# ============================================================

@app.callback(
    Output("download-csv", "data"),
    Input("export-csv", "n_clicks"),
    State("excel-data-store", "data"),
    prevent_initial_call=True
)
def export_csv(n_clicks, dataframe_json):

    if dataframe_json is None:
        return None

    dataframe = pd.read_json(
        io.StringIO(dataframe_json),
        orient="split"
    )

    return dcc.send_data_frame(
        dataframe.to_csv,
        "datos.csv",
        index=False
    )


# ============================================================
# CALLBACK 5
# DESCARGAR GRÁFICA EN PNG
# ============================================================

@app.callback(
    Output("download-png", "data"),
    Input("export-png", "n_clicks"),
    State("current-figure-store", "data"),
    prevent_initial_call=True
)
def export_png(n_clicks, figure_data):

    if figure_data is None:
        return None

    figure = go.Figure(figure_data)

    image_bytes = figure.to_image(
        format="png",
        width=1200,
        height=600,
        scale=2
    )

    return dcc.send_bytes(
        image_bytes,
        "grafica.png"
    )


# ============================================================
# CALLBACK 6
# DESCARGAR REPORTE DE CALIDAD
# ============================================================

@app.callback(
    Output("download-report", "data"),
    Input("export-report", "n_clicks"),
    State("analysis-store", "data"),
    prevent_initial_call=True
)
def export_report(n_clicks, analysis):

    if analysis is None:
        return None

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
    )


# ============================================================
# EJECUAR APLICACIÓN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )