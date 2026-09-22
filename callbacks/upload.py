"""
Callback de carga del archivo Excel: validación (extensión, tamaño,
archivo vacío), deduplicación de columnas, análisis y poblamiento de
todas las secciones dependientes del archivo.
"""

from dataclasses import dataclass
from typing import Any, cast
import base64
import io

import pandas as pd
from dash import Input, Output, State, html, dash_table

from app_instance import app, analyzer
from config import (
    ALLOWED_UPLOAD_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
)
from core.helpers import user_facing_error
from core.security import require_session
from services.excel_analyzer import ExcelAnalyzer


# ============================================================
# CALLBACK 1
# CARGAR Y ANALIZAR EXCEL
# ============================================================

HIDDEN_SECTION = {"display": "none"}
SHOWN_SECTION = {}


@dataclass
class _UploadState:
    """
    Estado completo que devuelve el callback `process_excel`.

    Antes esta respuesta era una tupla de 14 elementos sin nombre que
    debía casar *por posición* con los 14 `Output` del decorador. Cualquier
    reordenamiento o adición de un `Output` producía un error en runtime
    (o, peor, un valor asignado silenciosamente al componente equivocado).

    Con este dataclass los campos tienen nombre y el `return` se escribe
    como `_UploadState(...)`, de modo que es imposible intercambiar dos
    valores sin que su nombre lo delate.
    """

    file_status: Any
    file_info: Any
    data_preview: Any
    columns_section: Any
    column_options: Any
    secondary_options: Any
    excel_data: Any
    analysis: Any
    file_info_style: dict
    data_preview_style: dict
    columns_section_style: dict
    chart_builder_style: dict
    chart_result_style: dict

    def as_outputs(self) -> tuple:
        """
        Devuelve los valores en el MISMO orden que declara el decorador
        `@app.callback` de `process_excel`. Es el único punto donde el
        orden importa, y está junto al propio callback para poder
        verificarlo de un vistazo.
        """

        return (
            self.file_status,
            self.file_info,
            self.data_preview,
            self.columns_section,
            self.column_options,
            self.secondary_options,
            self.excel_data,
            self.analysis,
            self.file_info_style,
            self.data_preview_style,
            self.columns_section_style,
            self.chart_builder_style,
            self.chart_result_style,
        )


def _empty_upload_state(status_children) -> _UploadState:
    """
    Construye el estado "sin archivo / archivo inválido" dejando todas
    las secciones dependientes del archivo vacías y OCULTAS (no tiene
    sentido mostrar "Vista previa", "Crear gráfica" o "Resultado" con
    tarjetas en blanco cuando no hay ningún archivo cargado, o cuando
    la carga falló/está vacía).
    Evita repetir el estado en cada rama de validación.
    """

    return _UploadState(
        file_status=status_children,
        file_info="",
        data_preview="",
        columns_section="",
        column_options=[],
        secondary_options=[],
        excel_data=None,
        analysis=None,
        file_info_style=HIDDEN_SECTION,
        data_preview_style=HIDDEN_SECTION,
        columns_section_style=HIDDEN_SECTION,
        chart_builder_style=HIDDEN_SECTION,
        chart_result_style=HIDDEN_SECTION,
    )


@app.callback(
    Output("file-status", "children"),
    Output("file-info", "children"),
    Output("data-preview", "children"),
    Output("columns-section", "children"),
    Output("column-selector", "options"),
    Output("secondary-column-selector", "options"),
    Output("excel-data-store", "data"),
    Output("analysis-store", "data"),
    Output("file-info", "style"),
    Output("data-preview", "style"),
    Output("columns-section", "style"),
    Output("chart-builder-section", "style"),
    Output("chart-result-section", "style"),

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

    require_session()

    if contents is None:
        return _empty_upload_state("").as_outputs()

    # ========================================================
    # VALIDAR EXTENSIÓN ANTES DE LEER EL ARCHIVO
    # ========================================================

    filename_lower = (filename or "").lower()

    if not filename_lower.endswith(ALLOWED_UPLOAD_EXTENSIONS):

        return _empty_upload_state(
            html.Div(
                "❌ Formato no soportado. Solo se aceptan archivos "
                f"{' o '.join(ALLOWED_UPLOAD_EXTENSIONS)}.",
                className="error-message"
            )
        ).as_outputs()

    try:

        # ====================================================
        # DECODIFICAR
        # ====================================================

        content_type, content_string = contents.split(",")

        decoded = base64.b64decode(
            content_string
        )

        # ====================================================
        # VALIDAR TAMAÑO (defensa adicional al límite del
        # componente dcc.Upload, que solo se aplica en el cliente)
        # ====================================================

        if len(decoded) > MAX_FILE_SIZE_BYTES:

            return _empty_upload_state(
                html.Div(
                    f"❌ El archivo supera el límite de "
                    f"{MAX_FILE_SIZE_MB} MB permitido.",
                    className="error-message"
                )
            ).as_outputs()

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
        # NORMALIZAR COLUMNAS DUPLICADAS
        # ====================================================
        # Un Excel con dos encabezados iguales rompería la detección de
        # tipos y la generación de gráficas más adelante, ya que
        # dataframe["columna"] devolvería un DataFrame en vez de una
        # Serie. Se renombran para que cada columna sea única.

        dataframe = ExcelAnalyzer.deduplicate_columns(dataframe)

        # ====================================================
        # ARCHIVO SIN FILAS DE DATOS
        # ====================================================
        # Un Excel con solo encabezados (o completamente vacío) no
        # tiene sentido analizar ni graficar; se avisa explícitamente
        # en vez de dejar que fallen las secciones dependientes.

        if dataframe.shape[0] == 0:

            return _empty_upload_state(
                html.Div(
                    [
                        html.Span("⚠️ ", className="warning-icon"),
                        html.Span(
                            f"{filename} no contiene filas de datos "
                            "para analizar (solo encabezados)."
                        )
                    ],
                    className="warning-message"
                )
            ).as_outputs()

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
            # ESTADÍSTICAS DESCRIPTIVAS (solo numéricas) Y BADGE DE ID
            # ====================================================
            # El badge de identificador es independiente de las
            # estadísticas: una columna de folios alfanuméricos (texto)
            # puede ser un identificador sin tener estadísticas numéricas.

            statistics = column.get("statistics", {})
            is_identifier = bool(column.get("identifier"))

            if statistics:

                identifier_badge = " · 🔑 ID" if is_identifier else ""

                details.append(
                    html.Small(
                        f"Promedio {statistics.get('mean', '—')} · "
                        f"Mín {statistics.get('min', '—')} · "
                        f"Máx {statistics.get('max', '—')}"
                        f"{identifier_badge}",

                        className="column-stats"
                    )
                )

            elif is_identifier:

                details.append(
                    html.Small(
                        "🔑 Parece un identificador/folio (valores únicos "
                        "consecutivos)",

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
            _UploadState(
                file_status=status,
                file_info=info,
                data_preview=preview,
                columns_section=columns_view,
                column_options=column_options,
                secondary_options=secondary_options,
                excel_data=dataframe_json,
                analysis=result,
                file_info_style=SHOWN_SECTION,
                data_preview_style=SHOWN_SECTION,
                columns_section_style=SHOWN_SECTION,
                chart_builder_style=SHOWN_SECTION,
                chart_result_style=SHOWN_SECTION,
            ).as_outputs()
        )

    except Exception as error:

        return _empty_upload_state(
            user_facing_error(
                f"Error al procesar el archivo '{filename}'",
                error
            )
        ).as_outputs()
