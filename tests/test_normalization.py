import pandas as pd

from services.normalization import clean_numeric_text, looks_numeric, to_numeric


def test_clean_numeric_text_thousands_separator():
    series = pd.Series(["12,000", "15,500", "13,200"])

    cleaned = clean_numeric_text(series)

    assert cleaned.tolist() == ["12000", "15500", "13200"]


def test_clean_numeric_text_currency_symbols():
    series = pd.Series(["$120.50", "€99.99", "£150.00"])

    cleaned = clean_numeric_text(series)

    assert cleaned.tolist() == ["120.50", "99.99", "150.00"]


def test_to_numeric_numeric_series():
    series = pd.Series([1, 2, 3])

    result = to_numeric(series)

    assert result.dtype.kind in ("i", "f")
    assert result.tolist() == [1, 2, 3]


def test_to_numeric_text_series():
    series = pd.Series(["12,000", "15,500", None])

    result = to_numeric(series)

    assert pd.isna(result.iloc[2])
    assert result.iloc[0] == 12000
    assert result.iloc[1] == 15500


def test_to_numeric_scientific_notation():
    series = pd.Series(["1.23E+05", "2.0E+05"])

    result = to_numeric(series)

    assert result.iloc[0] == 123000
    assert result.iloc[1] == 200000


def test_looks_numeric_true():
    series = pd.Series(["12,000", "15,500", "13,200"])

    assert looks_numeric(series) is True


def test_looks_numeric_numeric_dtype():
    series = pd.Series([10, 20, 30])

    assert looks_numeric(series) is True


def test_looks_numeric_false_for_dates():
    series = pd.Series(["10/01/2024", "15/03/2024", "20/06/2024"])

    assert looks_numeric(series) is False