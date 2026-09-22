import pandas as pd

from services.excel_analyzer import ExcelAnalyzer


def test_numeric_column():
    analyzer = ExcelAnalyzer()

    series = pd.Series([10, 20, 30, 40])

    assert analyzer.detect_column_type(series) == "numeric"


def test_date_column():
    analyzer = ExcelAnalyzer()

    series = pd.Series([
        "10/01/2024",
        "15/03/2024",
        "20/06/2024",
        "05/02/2024"
    ])

    assert analyzer.detect_column_type(series) == "date"


def test_categorical_column():
    analyzer = ExcelAnalyzer()

    series = pd.Series([
        "Sistemas",
        "Ventas",
        "Sistemas",
        "RH",
        "Ventas"
    ])

    assert analyzer.detect_column_type(series) == "categorical"


def test_text_column():
    analyzer = ExcelAnalyzer()

    series = pd.Series([
        "Juan Pérez",
        "Ana López",
        "Pedro García",
        "María Torres",
        "Luis Hernández",
        "Carlos Ramírez",
        "Sofía Martínez",
        "Miguel González",
        "Laura Sánchez",
        "Daniel Rodríguez",
        "Fernando Díaz",
        "Gabriela Flores"
    ])

    assert analyzer.detect_column_type(series) == "text"


def test_missing_values():
    analyzer = ExcelAnalyzer()

    dataframe = pd.DataFrame({
        "Nombre": ["Juan", "Ana", None],
        "Edad": [25, 30, 28]
    })

    result = analyzer.analyze(dataframe)

    assert result["rows"] == 3
    assert result["columns"] == 2

    nombre = result["column_info"][0]

    assert nombre["missing"] == 1


def test_numeric_with_thousands_separator():
    analyzer = ExcelAnalyzer()

    series = pd.Series([
        "12,000",
        "15,500",
        "13,200",
        "18,900"
    ])

    assert analyzer.detect_column_type(series) == "numeric"


def test_numeric_with_currency_symbol():
    analyzer = ExcelAnalyzer()

    series = pd.Series([
        "$120.50",
        "$99.99",
        "$150.00"
    ])

    assert analyzer.detect_column_type(series) == "numeric"


def test_numeric_with_scientific_notation():
    analyzer = ExcelAnalyzer()

    series = pd.Series([
        "1.23E+05",
        "2.0E+05",
        "1.5E+05"
    ])

    assert analyzer.detect_column_type(series) == "numeric"


def test_column_statistics():
    analyzer = ExcelAnalyzer()

    dataframe = pd.DataFrame({
        "Salario": ["12,000", "15,500", "13,200", "18,900"]
    })

    result = analyzer.analyze(dataframe)

    salario = result["column_info"][0]

    assert "statistics" in salario
    assert salario["statistics"]["min"] == 12000
    assert salario["statistics"]["max"] == 18900


def test_identifier_detection():
    analyzer = ExcelAnalyzer()

    dataframe = pd.DataFrame({
        "ID": [1001, 1002, 1003, 1004],
        "Edad": [25, 30, 28, 35]
    })

    result = analyzer.analyze(dataframe)

    ids = result["column_info"][0]

    assert ids["type"] == "numeric"
    assert ids.get("identifier") is True


def test_quality_summary_present():
    analyzer = ExcelAnalyzer()

    dataframe = pd.DataFrame({
        "A": [1, 2, None],
        "B": ["x", "x", "y"]
    })

    result = analyzer.analyze(dataframe)

    assert "quality_summary" in result
    assert "completeness_score" in result["quality_summary"]
    assert result["quality_summary"]["duplicate_rows"] >= 0


def test_code_like_strings_not_detected_as_dates():
    analyzer = ExcelAnalyzer()

    # Cadenas tipo código (M1, S3...) no deben confundirse con fechas
    series = pd.Series(["M1", "M2", "M3", "M1", "M2", "M3"])

    assert analyzer.detect_column_type(series) == "categorical"


def test_dates_with_hours_are_detected():
    analyzer = ExcelAnalyzer()

    series = pd.Series([
        "10/01/2024 14:30:00",
        "15/03/2024 09:15:00",
        "20/06/2024 22:45:00"
    ])

    assert analyzer.detect_column_type(series) == "date"


# ================================================================
# DEDUPLICACIÓN DE COLUMNAS (regresión de bug: encabezados repetidos
# en el Excel rompían dataframe[columna] al devolver un DataFrame en
# vez de una Serie)
# ================================================================

def test_deduplicate_columns_renames_repeated_headers():
    dataframe = pd.DataFrame(
        [[1, 2, 3]],
        columns=["Ventas", "Ventas", "Costo"]
    )

    result = ExcelAnalyzer.deduplicate_columns(dataframe)

    assert list(result.columns) == ["Ventas", "Ventas_2", "Costo"]


def test_deduplicate_columns_handles_multiple_repeats():
    dataframe = pd.DataFrame(
        [[1, 2, 3, 4]],
        columns=["A", "A", "A", "B"]
    )

    result = ExcelAnalyzer.deduplicate_columns(dataframe)

    assert list(result.columns) == ["A", "A_2", "A_3", "B"]


def test_deduplicate_columns_avoids_collision_with_existing_name():
    # Si ya existe una columna llamada "A_2", el renombrado debe
    # seguir generando nombres únicos sin chocar con ella.
    dataframe = pd.DataFrame(
        [[1, 2, 3]],
        columns=["A", "A", "A_2"]
    )

    result = ExcelAnalyzer.deduplicate_columns(dataframe)

    assert len(set(result.columns)) == 3


def test_deduplicate_columns_leaves_unique_columns_untouched():
    dataframe = pd.DataFrame(
        [[1, 2, 3]],
        columns=["A", "B", "C"]
    )

    result = ExcelAnalyzer.deduplicate_columns(dataframe)

    assert list(result.columns) == ["A", "B", "C"]

    # Cada columna sigue siendo accesible como Serie, no como DataFrame
    assert isinstance(result["A"], pd.Series)


# ================================================================
# DATAFRAME SIN FILAS (regresión de bug: un Excel con solo
# encabezados debía manejarse sin lanzar excepciones)
# ================================================================

def test_analyze_handles_empty_dataframe():
    analyzer = ExcelAnalyzer()

    dataframe = pd.DataFrame(columns=["A", "B"])

    result = analyzer.analyze(dataframe)

    assert result["rows"] == 0
    assert result["columns"] == 2
    assert result["quality_summary"]["completeness_score"] == 100


# ================================================================
# GRUPO 2 · ítem 7: detección de fechas por muestreo en columnas
# grandes (no debe cambiar el resultado, solo el rendimiento)
# ================================================================

def test_date_detection_still_works_on_large_column():
    analyzer = ExcelAnalyzer()

    # Más filas que TYPE_DETECTION_SAMPLE_SIZE para forzar el muestreo
    dates = pd.date_range("2023-01-01", periods=1200, freq="D")
    series = pd.Series(dates.strftime("%d/%m/%Y"))

    assert analyzer.detect_column_type(series) == "date"


def test_non_date_column_still_rejected_when_large():
    analyzer = ExcelAnalyzer()

    # Columna de texto grande y no fechas: no debe clasificarse como date
    series = pd.Series([f"Cliente {i}" for i in range(1200)])

    assert analyzer.detect_column_type(series) != "date"


# ================================================================
# GRUPO 2 · ítem 8: estadísticas solo para columnas numéricas
# ================================================================

def test_statistics_only_computed_for_numeric_columns():
    analyzer = ExcelAnalyzer()

    dataframe = pd.DataFrame({
        "Ventas": [100, 200, 300],
        "Region": ["Norte", "Sur", "Norte"],
    })

    result = analyzer.analyze(dataframe)

    by_name = {column["name"]: column for column in result["column_info"]}

    assert by_name["Ventas"]["statistics"] != {}
    assert by_name["Region"]["statistics"] == {}


# ================================================================
# GRUPO 2 · ítem 9: identificadores alfanuméricos (folios)
# ================================================================

def test_alphanumeric_identifier_detected():
    analyzer = ExcelAnalyzer()

    series = pd.Series(["FOLIO-001", "FOLIO-002", "FOLIO-003", "FOLIO-004"])

    # Con pocos valores únicos, el tipo detectado es "categorical" (no
    # "text"); lo relevante aquí es que el detector de identificador lo
    # reconozca igual como secuencia de folios.
    assert analyzer.detect_column_type(series) in ("categorical", "text")
    assert analyzer._is_identifier(series) is True


def test_alphanumeric_identifier_rejects_inconsistent_prefix():
    analyzer = ExcelAnalyzer()

    series = pd.Series(["FOLIO-001", "ORDEN-002", "FOLIO-003"])

    assert analyzer._is_identifier(series) is False


def test_alphanumeric_identifier_rejects_non_sequential_numbers():
    analyzer = ExcelAnalyzer()

    series = pd.Series(["FOLIO-001", "FOLIO-050", "FOLIO-777"])

    assert analyzer._is_identifier(series) is False


def test_alphanumeric_identifier_rejects_duplicates():
    analyzer = ExcelAnalyzer()

    series = pd.Series(["FOLIO-001", "FOLIO-001", "FOLIO-002"])

    assert analyzer._is_identifier(series) is False


def test_analyze_marks_identifier_on_text_column():
    analyzer = ExcelAnalyzer()

    dataframe = pd.DataFrame({
        "Folio": ["A1001", "A1002", "A1003"],
        "Cliente": ["Ana", "Beto", "Ana"],
    })

    result = analyzer.analyze(dataframe)

    by_name = {column["name"]: column for column in result["column_info"]}

    assert by_name["Folio"]["identifier"] is True
    assert by_name["Cliente"].get("identifier", False) is False


def test_analyze_marks_identifier_on_large_alphanumeric_column():
    analyzer = ExcelAnalyzer()

    # Más de 10 valores únicos: aquí sí debe clasificarse como "text"
    # (unique_ratio 100% supera cualquier umbral categórico).
    folios = [f"ORD-{i:04d}" for i in range(1, 30)]
    dataframe = pd.DataFrame({"Folio": folios})

    result = analyzer.analyze(dataframe)
    folio_info = result["column_info"][0]

    assert folio_info["type"] == "text"
    assert folio_info["identifier"] is True