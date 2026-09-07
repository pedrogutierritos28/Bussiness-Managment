import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from services.normalization import to_numeric


class ChartGenerator:
    """
    Genera gráficas a partir de un DataFrame de Pandas.
    """

    # ============================================================
    # TIPOS DE GRÁFICAS DISPONIBLES
    # ============================================================

    CHART_TYPES = {
        "bar": "Barras",
        "line": "Línea",
        "pie": "Pastel",
        "histogram": "Histograma",
        "box": "Caja y bigotes",
        "scatter": "Dispersión",
    }

    # Rangos de agrupación temporal disponibles para series de fechas.
    # Frecuencias válidas para pd.Series.dt.to_period en pandas 3.x
    TIME_GROUPS = {
        "D": "Diario",
        "W": "Semanal",
        "M": "Mensual",
        "Q": "Trimestral",
        "Y": "Anual",
    }

    # Funciones de agregación disponibles para resumir datos
    AGG_FUNCTIONS = {
        "count": "Conteo",
        "sum": "Suma",
        "mean": "Promedio",
        "min": "Mínimo",
        "max": "Máximo",
    }

    # ============================================================
    # OBTENER GRÁFICAS COMPATIBLES
    # ============================================================

    def get_available_charts(self, column_type: str) -> list[dict]:
        """
        Devuelve las gráficas apropiadas según el tipo de columna.
        """

        if column_type == "numeric":
            return [
                {
                    "value": "bar",
                    "label": "📊 Barras"
                },
                {
                    "value": "line",
                    "label": "📈 Línea"
                },
                {
                    "value": "histogram",
                    "label": "📉 Histograma"
                },
                {
                    "value": "box",
                    "label": "📦 Caja y bigotes"
                },
                {
                    "value": "scatter",
                    "label": "✦ Dispersión"
                },
            ]

        if column_type == "categorical":
            return [
                {
                    "value": "bar",
                    "label": "📊 Barras"
                },
                {
                    "value": "pie",
                    "label": "🥧 Pastel"
                },
            ]

        if column_type == "date":
            return [
                {
                    "value": "line",
                    "label": "📈 Línea"
                },
                {
                    "value": "bar",
                    "label": "📊 Barras"
                },
                {
                    "value": "histogram",
                    "label": "📉 Histograma"
                },
            ]

        if column_type == "boolean":
            return [
                {
                    "value": "bar",
                    "label": "📊 Barras"
                },
                {
                    "value": "pie",
                    "label": "🥧 Pastel"
                },
            ]

        # Texto libre
        return [
            {
                "value": "bar",
                "label": "📊 Barras"
            }
        ]

    # ============================================================
    # GENERAR GRÁFICA
    # ============================================================

    def generate(
        self,
        dataframe: pd.DataFrame,
        column: str,
        chart_type: str,
        period: str | None = None,
        secondary_column: str | None = None,
        nbins: int | None = None,
        group_by: str | None = None,
        agg: str | None = None,
    ) -> go.Figure:
        """
        Genera una gráfica utilizando la columna seleccionada.

        Parámetros opcionales:
        - period: frecuencia de agrupación ('D', 'W', 'M', 'Q', 'Y')
          para series temporales. Si no se indica, se infiere del rango.
        - secondary_column: segunda columna numérica para dispersión (X).
        - nbins: número de barras para histogramas.
        - group_by: columna categórica o fecha para resumir datos
          (solo aplica a bar, line y pie).
        - agg: función de agregación ('count', 'sum', 'mean', 'min', 'max').
          Requiere group_by.
        """

        if column not in dataframe.columns:
            raise ValueError(
                f"La columna '{column}' no existe."
            )

        if secondary_column and secondary_column not in dataframe.columns:
            raise ValueError(
                f"La columna '{secondary_column}' no existe."
            )

        if group_by and group_by not in dataframe.columns:
            raise ValueError(
                f"La columna de agrupación '{group_by}' no existe."
            )

        if agg and agg not in self.AGG_FUNCTIONS:
            raise ValueError(
                f"Función de agregación no soportada: {agg}"
            )

        if chart_type not in self.CHART_TYPES:
            raise ValueError(
                f"Tipo de gráfica no soportado: {chart_type}"
            )

        series = dataframe[column]

        # ========================================================
        # AGREGACIÓN OPCIONAL (resumir por columna categórica/fecha)
        # ========================================================

        aggregated = bool(group_by and agg)
        agg_mode = False
        value_label = column
        x_col = column
        y_col = column

        if aggregated and chart_type in ("bar", "line", "pie"):
            assert group_by is not None
            assert agg is not None

            # Numericizar la columna de valores antes de agregar
            # (aunque venga como texto: separadores/notación científica)
            numeric_col = self._as_numeric(dataframe[column])

            plot_frame = dataframe.copy()
            plot_frame[column] = numeric_col

            if agg == "count":
                plot_data = (
                    plot_frame
                    .groupby(group_by, dropna=False)
                    .size()
                    .reset_index(name="Cantidad")
                )
                x_col = group_by
                y_col = "Cantidad"
                value_label = "Cantidad"
            else:
                plot_data = (
                    plot_frame
                    .groupby(group_by, dropna=False)[column]
                    .agg(agg)
                    .reset_index()
                )
                plot_data.columns = [group_by, column]
                x_col = group_by
                y_col = column
                value_label = f"{self.AGG_FUNCTIONS[agg]} de {column}"

            series = plot_data[y_col]
            agg_mode = True
        else:
            plot_data = dataframe

        # ========================================================
        # BARRAS
        # ========================================================

        if chart_type == "bar":

            if agg_mode:

                figure = px.bar(
                    plot_data,
                    x=x_col,
                    y=y_col,
                    title=f"{value_label} por {x_col}"
                )

            elif pd.api.types.is_numeric_dtype(series):

                figure = px.bar(
                    dataframe,
                    x=column,
                    title=f"Distribución de {column}"
                )

            else:

                counts = (
                    series
                    .value_counts()
                    .reset_index()
                )

                counts.columns = [
                    column,
                    "Cantidad"
                ]

                figure = px.bar(
                    counts,
                    x=column,
                    y="Cantidad",
                    title=f"Distribución de {column}"
                )

        # ========================================================
        # LÍNEA
        # ========================================================

        elif chart_type == "line":

            if agg_mode:

                figure = px.line(
                    plot_data,
                    x=x_col,
                    y=y_col,
                    markers=True,
                    title=f"{value_label} por {x_col}"
                )

            elif pd.api.types.is_datetime64_any_dtype(series):

                # Periodo configurable o inferido según el rango de datos
                period = period or self._infer_time_period(
                    series.astype("datetime64[ns]")
                )

                grouped = (
                    series
                    .astype("datetime64[ns]")
                    .dt.to_period(period)
                    .dt.to_timestamp()
                    .value_counts()
                    .sort_index()
                    .reset_index()
                )

                grouped.columns = [
                    column,
                    "Cantidad"
                ]

                figure = px.line(
                    grouped,
                    x=column,
                    y="Cantidad",
                    markers=True,
                    title=f"Registros por {column} ({self.TIME_GROUPS.get(period, period)})"
                )

            else:

                figure = px.line(
                    dataframe,
                    y=column,
                    markers=True,
                    title=f"Evolución de {column}"
                )

        # ========================================================
        # PASTEL
        # ========================================================

        elif chart_type == "pie":

            if agg_mode:

                figure = px.pie(
                    plot_data,
                    names=x_col,
                    values=y_col,
                    title=f"{value_label} por {x_col}"
                )

            else:

                counts = (
                    series
                    .value_counts()
                    .reset_index()
                )

                counts.columns = [
                    column,
                    "Cantidad"
                ]

                figure = px.pie(
                    counts,
                    names=column,
                    values="Cantidad",
                    title=f"Distribución de {column}"
                )

        # ========================================================
        # HISTOGRAMA
        # ========================================================

        elif chart_type == "histogram":

            figure = px.histogram(
                dataframe,
                x=column,
                nbins=nbins,
                title=f"Distribución de {column}"
            )

        # ========================================================
        # CAJA Y BIGOTES
        # ========================================================

        elif chart_type == "box":

            figure = px.box(
                dataframe,
                y=column,
                title=f"Distribución de {column}",
                points="outliers"
            )

        # ========================================================
        # DISPERSIÓN
        # ========================================================

        elif chart_type == "scatter":

            # Dispersión de dos variables numéricas con línea de tendencia
            if secondary_column:

                x_series = self._as_numeric(series)
                y_series = self._as_numeric(dataframe[secondary_column])

                figure = px.scatter(
                    x=x_series,
                    y=y_series,
                    title=f"{column} vs {secondary_column}",
                    labels={"x": column, "y": secondary_column}
                )

                self._add_trend_line(
                    figure,
                    x_series,
                    y_series
                )

            # Dispersión simple de una variable (orden de filas)
            else:

                y_series = self._as_numeric(series)

                figure = px.scatter(
                    x=dataframe.index,
                    y=y_series,
                    title=f"Dispersión de {column}",
                    labels={"x": "Índice", "y": column}
                )

        else:

            raise ValueError(
                f"No se pudo generar la gráfica: {chart_type}"
            )

        # ========================================================
        # CONFIGURACIÓN GENERAL
        # ========================================================

        figure.update_layout(
            template="plotly_white",
            margin=dict(
                l=40,
                r=40,
                t=70,
                b=40
            ),
            hovermode="closest"
        )

        return figure

    def _infer_time_period(self, series: pd.Series) -> str:
        """
        Infiere la unidad de agrupación temporal idónea para una serie
        de fechas, basándose en el rango de tiempo abarcado.

        Devuelve una frecuencia válida para pd.to_period
        ('D', 'W', 'M', 'Q', 'Y').
        """

        if series.empty:
            return "M"

        try:
            days = (series.max() - series.min()).days

            if days <= 45:
                return "D"
            if days <= 180:
                return "W"
            if days <= 800:
                return "M"
            if days <= 1500:
                return "Q"
            return "Y"
        except (TypeError, ValueError):
            return "M"

    def _as_numeric(self, series: pd.Series) -> pd.Series:
        """
        Convierte una serie a numérica, limpiando previamente
        separadores de miles y símbolos de moneda.
        """

        return to_numeric(series)

    def _add_trend_line(
        self,
        figure: go.Figure,
        x: pd.Series,
        y: pd.Series
    ) -> None:
        """
        Añade una recta de tendencia (regresión lineal simple) a un gráfico
        de dispersión usando numpy, sin dependencias adicionales.
        """

        clean = pd.concat([x, y], axis=1).dropna()

        if len(clean) < 2:
            return

        xv = clean.iloc[:, 0].astype(float).to_numpy()
        yv = clean.iloc[:, 1].astype(float).to_numpy()

        slope, intercept = np.polyfit(xv, yv, 1)

        x_range = np.linspace(xv.min(), xv.max(), 50)

        figure.add_trace(
            go.Scatter(
                x=x_range,
                y=slope * x_range + intercept,
                mode="lines",
                name="Tendencia",
                line={
                    "color": "rgba(220, 38, 38, 0.8)",
                    "dash": "dash",
                    "width": 2,
                },
                hovertemplate="y = %{y:.2f}<extra>Tendencia</extra>",
            )
        )