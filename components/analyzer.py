"""
Layout de la vista principal del analizador (lo que ve el usuario tras
iniciar sesión). El layout de login vive en `components/login.py`.
"""

from dash import dcc, html

from config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB


def analyzer_layout():
    return html.Div(
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
                ),

                html.Button(
                    "Cerrar sesión",
                    id="logout-button",
                    className="logout-button",
                    n_clicks=0
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

                            # Límite de tamaño en bytes: rechaza archivos
                            # demasiado grandes antes de intentar leerlos.
                            max_size=MAX_FILE_SIZE_BYTES,

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
                                        f"Formatos compatibles: .xlsx, .xls "
                                        f"· Máximo {MAX_FILE_SIZE_MB} MB",
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
                    className="file-info-section",
                    style={"display": "none"}
                ),

                # ==================================================
                # VISTA PREVIA
                # ==================================================

                html.Section(
                    id="data-preview",
                    className="preview-section",
                    style={"display": "none"}
                ),

                # ==================================================
                # COLUMNAS DETECTADAS
                # ==================================================

                html.Section(
                    id="columns-section",
                    className="columns-section",
                    style={"display": "none"}
                ),

                # ==================================================
                # GENERADOR DE GRÁFICAS
                # ==================================================

                html.Section(
                    id="chart-builder-section",
                    className="chart-builder-section",
                    style={"display": "none"},

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

                    style={"display": "none"},

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

                        html.Div(
                            id="chart-placeholder",
                            className="chart-placeholder",
                            children=(
                                "📊 Aquí aparecerá tu gráfica una vez que "
                                "la generes."
                            )
                        ),

                        dcc.Graph(
                            id="chart-output",

                            style={
                                "width": "100%",
                                "height": "600px",
                                "display": "none"
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
