import pandas as pd
from plotly.graph_objects import Figure

from services.chart_generator import ChartGenerator


def create_test_dataframe():
    return pd.DataFrame({
        "Departamento": [
            "Sistemas",
            "Recursos Humanos",
            "Sistemas",
            "Ventas",
            "Ventas"
        ],

        "Edad": [
            25,
            31,
            28,
            35,
            29
        ],

        "Salario": [
            12000,
            15000,
            13500,
            18000,
            14500
        ]
    })


def test_numeric_chart_options():

    generator = ChartGenerator()

    charts = generator.get_available_charts(
        "numeric"
    )

    values = [
        chart["value"]
        for chart in charts
    ]

    assert "bar" in values
    assert "line" in values
    assert "histogram" in values


def test_categorical_chart_options():

    generator = ChartGenerator()

    charts = generator.get_available_charts(
        "categorical"
    )

    values = [
        chart["value"]
        for chart in charts
    ]

    assert "bar" in values
    assert "pie" in values


def test_generate_bar_chart():

    generator = ChartGenerator()

    dataframe = create_test_dataframe()

    figure = generator.generate(
        dataframe,
        "Departamento",
        "bar"
    )

    assert figure is not None


def test_generate_pie_chart():

    generator = ChartGenerator()

    dataframe = create_test_dataframe()

    figure = generator.generate(
        dataframe,
        "Departamento",
        "pie"
    )

    assert figure is not None


def test_generate_histogram():

    generator = ChartGenerator()

    dataframe = create_test_dataframe()

    figure = generator.generate(
        dataframe,
        "Salario",
        "histogram"
    )

    assert figure is not None


def test_numeric_box_chart_option():

    generator = ChartGenerator()

    charts = generator.get_available_charts(
        "numeric"
    )

    values = [
        chart["value"]
        for chart in charts
    ]

    assert "box" in values


def test_numeric_scatter_chart_option():

    generator = ChartGenerator()

    charts = generator.get_available_charts(
        "numeric"
    )

    values = [
        chart["value"]
        for chart in charts
    ]

    assert "scatter" in values


def test_generate_scatter_with_secondary_column():

    generator = ChartGenerator()

    dataframe = create_test_dataframe()

    figure = generator.generate(
        dataframe,
        "Salario",
        "scatter",
        secondary_column="Edad"
    )

    assert figure is not None
    assert len(figure.data) == 2


def test_generate_scatter_simple_uses_row_label():

    generator = ChartGenerator()

    dataframe = create_test_dataframe()

    figure = generator.generate(
        dataframe,
        "Salario",
        "scatter"
    )

    assert figure is not None
    # El eje X debe decir "Fila", no "index"/"Índice"
    assert figure.layout.xaxis.title.text == "Fila"
    # Numeración 1-based: la primera fila de datos es Fila 1
    first_row = figure.data[0].x[0]
    assert first_row == 1


def test_generate_line_numeric_uses_row_label():

    generator = ChartGenerator()

    dataframe = create_test_dataframe()

    figure = generator.generate(
        dataframe,
        "Salario",
        "line"
    )

    assert figure is not None
    # El eje X debe decir "Fila", no "index"
    assert figure.layout.xaxis.title.text == "Fila"
    # Numeración 1-based: la primera fila de datos es Fila 1
    first_row = figure.data[0].x[0]
    assert first_row == 1


def test_generate_histogram_with_nbins():

    generator = ChartGenerator()

    dataframe = create_test_dataframe()

    figure = generator.generate(
        dataframe,
        "Salario",
        "histogram",
        nbins=10
    )

    assert figure is not None


def test_generate_box_chart():

    generator = ChartGenerator()

    dataframe = create_test_dataframe()

    figure = generator.generate(
        dataframe,
        "Salario",
        "box"
    )

    assert figure is not None


def test_date_includes_histogram_option():

    generator = ChartGenerator()

    charts = generator.get_available_charts(
        "date"
    )

    values = [
        chart["value"]
        for chart in charts
    ]

    assert "histogram" in values


def test_infer_time_period_daily():

    generator = ChartGenerator()

    series = pd.Series(
        pd.to_datetime(["2026-01-01", "2026-01-15", "2026-02-01"])
    ).astype("datetime64[ns]")

    assert generator._infer_time_period(series) == "D"


def test_infer_time_period_monthly():

    generator = ChartGenerator()

    series = pd.Series(
        pd.to_datetime(["2026-01-01", "2026-03-01", "2026-08-01"])
    ).astype("datetime64[ns]")

    assert generator._infer_time_period(series) == "M"