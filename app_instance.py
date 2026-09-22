"""
Instancia de la aplicación Dash y singletons compartidos.

Este módulo existe para romper las importaciones circulares: los archivos
de `callbacks/` necesitan decorar sus funciones con `@app.callback` sin
importar `app.py` (que a su vez los importa a ellos para registrarlos).
Todos importan desde aquí:

    from app_instance import app, analyzer, chart_generator
"""

import os
import secrets

from dash import Dash

from config import logger
from services.excel_analyzer import ExcelAnalyzer
from services.chart_generator import ChartGenerator


app = Dash(
    __name__,
    title="CA Y LI Analyzer"
)

# ============================================================
# SESIÓN DEL LADO DEL SERVIDOR
# ============================================================
# Dash corre sobre Flask (app.server). Sin esto, "iniciar sesión" solo
# cambia lo que el navegador MUESTRA, pero cualquiera puede seguir
# invocando los callbacks directamente (p. ej. con curl) sin haberse
# autenticado nunca. flask.session guarda, en una cookie firmada con
# SECRET_KEY, que esta petición viene de un usuario ya autenticado; los
# callbacks sensibles verifican esa cookie antes de hacer cualquier cosa.
_secret_key = os.getenv("SECRET_KEY")

if not _secret_key:
    # No hay SECRET_KEY configurada (.env ausente o incompleto). Se genera
    # una temporal para que la app siga arrancando en desarrollo, pero
    # cambia en cada reinicio del servidor -> todas las sesiones activas
    # se invalidan. NUNCA debe pasar esto en producción.
    _secret_key = secrets.token_hex(32)
    logger.warning(
        "SECRET_KEY no configurada en el entorno (.env). Se generó una "
        "temporal solo para esta ejecución: las sesiones no sobrevivirán "
        "un reinicio del servidor. Define SECRET_KEY en producción."
    )

app.server.secret_key = _secret_key


# Instancias únicas compartidas por los callbacks (análisis del Excel y
# generación de gráficas).
analyzer = ExcelAnalyzer()
chart_generator = ChartGenerator()
