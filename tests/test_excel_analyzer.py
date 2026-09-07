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