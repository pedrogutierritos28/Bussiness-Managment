from pathlib import Path

import pandas as pd

from services.normalization import clean_numeric_text, looks_numeric, to_numeric


class ExcelAnalyzer:
    """
    Se encarga de cargar y analizar archivos Excel.
    """

    SUPPORTED_EXTENSIONS = {".xlsx", ".xls"}

    # Formatos de fecha compatibles con datos industriales
    DATE_FORMATS = [
        "%d/%m/%Y",      # 01/10/2024 - formato latinoamericano
        "%m/%d/%Y",      # 10/01/2024 - formato estadounidense
        "%Y-%m-%d",      # 2024-10-01 - formato ISO
        "%d-%m-%Y",      # 01-10-2024
        "%m-%d-%Y",      # 10-01-2024
        "%Y/%m/%d",      # 2024/10/01
        "%d.%m.%Y",      # 01.10.2024
        "%Y%m%d",        # 20241001 - compacto
    ]

    def load_file(self, file_path: str) -> pd.DataFrame:
        """
        Carga un archivo Excel y devuelve un DataFrame.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo: {file_path}"
            )

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Formato no soportado: {path.suffix}"
            )

        return pd.read_excel(path)

    def detect_column_type(self, series: pd.Series) -> str:
        """
        Detecta el tipo lógico de una columna con validación industrial.
        """

        # Eliminamos valores vacíos para analizar
        non_null = series.dropna()

        if non_null.empty:
            return "text"

        # Booleanos - verificar ambos dtype y valores de texto
        if pd.api.types.is_bool_dtype(series):
            return "boolean"

        # Determinar si la columna es de tipo textual (object o StringDtype)
        # En pandas 3.x los textos pueden tener dtype "str" en lugar de "object"
        is_textual = pd.api.types.is_object_dtype(series) or isinstance(
            series.dtype, pd.StringDtype
        )

        # Intentar detectar booleanos por valores de texto comunes
        if is_textual:
            lower_vals = series.astype(str).str.lower().str.strip()
            boolean_values = lower_vals.isin(["true", "false", "yes", "no", "1", "0", "verdad", "falso"])
            if boolean_values.mean() > 0.5:
                return "boolean"

        # Numéricos - incluir validación industrial
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"

        # Numéricos en formato texto - notación científica, separadores de
        # miles, decimales y símbolos de moneda propios de datos industriales
        if is_textual and self._looks_like_numeric(non_null):
            return "numeric"

        # Fechas - con múltiples formatos y validación de razón
        if self._looks_like_date_advanced(non_null, series):
            return "date"

        # Categóricas - validación mejorada con umbral adaptativo
        if self._looks_like_categorical_advanced(non_null, len(series)):
            return "categorical"

        # Texto normal
        return "text"

    def _looks_like_date_advanced(self, series: pd.Series, original_series: pd.Series) -> bool:
        """
        Determina si una serie parece contener fechas con validación industrial mejorada.
        """

        # No intentamos detectar fechas en columnas numéricas
        if pd.api.types.is_numeric_dtype(original_series):
            return False

        try:
            # Probar múltiples formatos y conservar el mejor resultado
            best_ratio = 0
            best_converted = None

            for fmt in self.DATE_FORMATS:
                try:
                    converted = pd.to_datetime(
                        series,
                        format=fmt,
                        errors="coerce"
                    )
                except (ValueError, TypeError):
                    continue

                ratio = converted.notna().mean()

                if ratio > best_ratio:
                    best_ratio = ratio
                    best_converted = converted

            # Si ninguno de los formatos básicos funciona, intentar mixed
            if best_converted is None:
                best_converted = pd.to_datetime(
                    series,
                    format="mixed",
                    errors="coerce"
                )
                best_ratio = best_converted.notna().mean()

            # Una columna es fecha si el 80% o más de los valores se pueden
            # parsear. Pero debe ser una fecha "plausible" (año 1900-2100):
            # el parser 'mixed' de pandas interpreta cadenas como "M1" o
            # "S3" como minutos/segundos (año 1), generando falsos positivos.
            if best_ratio >= 0.8:

                years = best_converted.dt.year

                plausible = best_converted[
                    (years >= 1900) & (years <= 2100)
                ]

                plausible_ratio = plausible.notna().mean()

                if plausible_ratio < 0.8:
                    return False

                return plausible.dropna().nunique() >= 3

            return False

        except (ValueError, TypeError):
            return False

    def _looks_like_categorical_advanced(self, series: pd.Series, total_count: int) -> bool:
        """
        Determina si una columna representa categorías con umbral adaptativo.
        """

        if total_count == 0:
            return False

        unique_count = series.nunique()

        # Si tiene muy pocos valores distintos (umbral fijo)
        if unique_count <= 10:
            return True

        # Umbral proporcional basado en el tamaño del dataset
        # Datasets pequeños: hasta 50% pueden ser categóricos
        # Datasets medianos: hasta 20% pueden ser categóricos
        # Datasets grandes: hasta 10% pueden ser categóricos
        if total_count <= 50:
            ratio_threshold = 0.50
        elif total_count <= 500:
            ratio_threshold = 0.20
        else:
            ratio_threshold = 0.10

        unique_ratio = unique_count / total_count

        return unique_ratio <= ratio_threshold

    def _clean_numeric(self, series: pd.Series) -> pd.Series:
        """
        Limpia una serie de texto eliminando separadores de miles y
        símbolos de moneda para intentar interpretarla como numérica.
        """

        return clean_numeric_text(series)

    def _looks_like_numeric(self, series: pd.Series) -> bool:
        """
        Determina si una serie de texto contiene principalmente datos
        numéricos, incluyendo notación científica (1.23E+05), separadores
        de miles (12,000) o símbolos de moneda ($120.50).
        """

        return looks_numeric(series)

    def _column_statistics(self, series: pd.Series) -> dict:
        """
        Calcula estadísticas descriptivas para una columna numérica.

        Soporta valores con separadores de miles y símbolos de moneda
        propios de datos industriales.
        """

        stats = {}

        parsed = to_numeric(series)

        if parsed.notna().sum() > 0:
            stats["mean"] = round(float(parsed.mean()), 2)
            stats["min"] = round(float(parsed.min()), 2)
            stats["max"] = round(float(parsed.max()), 2)
            stats["std"] = round(float(parsed.std()), 2)

        return stats

    def _is_identifier(self, series: pd.Series) -> bool:
        """
        Detecta si una columna parece un identificador/secuencia
        (valores únicos consecutivos, p. ej. IDs, folios o índices).
        """

        non_null = series.dropna()

        if non_null.empty:
            return False

        if not pd.api.types.is_numeric_dtype(non_null):
            return False

        # Todos los valores son únicos
        if non_null.nunique() != len(non_null):
            return False

        # Secuencia consecutiva (1,2,3,... o 1001,1002,...)
        try:
            sorted_values = non_null.sort_values().reset_index(drop=True)

            if len(sorted_values) < 2:
                return False

            diffs = sorted_values.diff().dropna()

            if diffs.empty:
                return False

            return bool((diffs == diffs.iloc[0]).all())
        except Exception:
            return False

    def analyze(self, dataframe: pd.DataFrame) -> dict:
        """
        Analiza un DataFrame y devuelve información estructurada con metadata de calidad.
        """

        columns = []

        for column in dataframe.columns:
            series = dataframe[column]

            column_type = self.detect_column_type(series)

            column_info = {
                "name": str(column),
                "type": column_type,
                "missing": int(series.isna().sum()),
                "empty_strings": int((series == "").sum()),
                "total_missing": int(series.isna().sum()) + int((series == "").sum()),
                "unique": int(series.nunique()),
                "total": len(series),
                "statistics": self._column_statistics(series),
            }

            if column_type == "numeric":
                column_info["identifier"] = self._is_identifier(series)

            columns.append(column_info)

        return {
            "rows": len(dataframe),
            "columns": len(dataframe.columns),
            "column_info": columns,
            "quality_summary": self._generate_quality_summary(dataframe),
        }

    def _generate_quality_summary(self, dataframe: pd.DataFrame) -> dict:
        """
        Genera un resumen de calidad de datos para el archivo completo.
        """

        total_cells = dataframe.size
        total_missing = dataframe.isna().sum().sum()
        total_empty_strings = (dataframe == "").sum().sum()
        total_duplicates = dataframe.duplicated().sum()

        return {
            "total_cells": total_cells,
            "missing_percentage": round((total_missing / total_cells) * 100, 2) if total_cells > 0 else 0,
            "empty_strings_percentage": round((total_empty_strings / total_cells) * 100, 2) if total_cells > 0 else 0,
            "duplicate_rows": int(total_duplicates),
            "completeness_score": round(
                ((total_cells - total_missing - total_empty_strings) / total_cells) * 100, 2
            ) if total_cells > 0 else 100,
        }