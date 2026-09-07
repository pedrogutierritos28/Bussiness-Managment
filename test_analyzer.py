from services.excel_analyzer import ExcelAnalyzer


def main():
    analyzer = ExcelAnalyzer()

    file_path = "uploads/prueba.xlsx"

    dataframe = analyzer.load_file(file_path)

    result = analyzer.analyze(dataframe)

    print("\n========== ANÁLISIS ==========\n")

    print(f"Filas: {result['rows']}")
    print(f"Columnas: {result['columns']}")

    print("\nColumnas detectadas:\n")

    for column in result["column_info"]:
        print(
            f"- {column['name']}"
            f" | Tipo: {column['type']}"
            f" | Vacíos: {column['missing']}"
            f" | Únicos: {column['unique']}"
        )


if __name__ == "__main__":
    main()