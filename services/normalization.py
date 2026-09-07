"""Utilidades compartidas para detección y normalización de datos numéricos.

Centraliza la lógica de limpieza de texto numérico (separadores de miles,
símbolos de moneda y notación científica) usada tanto por el analizador
como por el generador de gráficas, evitando duplicación.
"""

import pandas as pd

# Símbolos de moneda que se eliminan al interpretar texto como numérico
CURRENCY_SYMBOLS = ("$", "€", "£")


def clean_numeric_text(series: pd.Series) -> pd.Series:
    """
    Limpia una serie de texto eliminando espacios, separadores de miles
    y símbolos de moneda, para poder interpretarla como numérica.

    Ejemplos: "12,000" -> "12000"; "$120.50" -> "120.50".
    """

    text = (
        series
        .astype(str)
        .str.strip()
        .str.replace(",", "", regex=False)
    )

    for symbol in CURRENCY_SYMBOLS:
        text = text.str.replace(symbol, "", regex=False)

    return text


def to_numeric(series: pd.Series) -> pd.Series:
    """
    Convierte una serie a numérica. Si ya es numérica la devuelve como tal;
    en caso contrario limpia el texto antes de intentar la conversión,
    forzando errores a NaN.
    """

    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    return pd.to_numeric(
        clean_numeric_text(series),
        errors="coerce",
    )


def looks_numeric(series: pd.Series, threshold: float = 0.8) -> bool:
    """
    Indica si una serie de texto contiene principalmente datos numéricos,
    incluyendo notación científica (1.23E+05), separadores de miles (12,000)
    o símbolos de moneda ($120.50).
    """

    if pd.api.types.is_numeric_dtype(series):
        return True

    try:
        return bool(to_numeric(series).notna().mean() >= threshold)
    except (ValueError, TypeError, AttributeError):
        return False