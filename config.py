"""
Configuración global de la aplicación leída del entorno (.env).

Centraliza las constantes que antes vivían al inicio de app.py para que
cualquier módulo (callbacks, components, app_instance) las importe desde
un solo lugar sin importar el módulo principal.
"""

import logging
import os

from dotenv import load_dotenv


# Carga las variables de entorno desde .env (SUPABASE_URL,
# SUPABASE_ANON_KEY, SECRET_KEY, etc.). Antes .env existía pero nadie lo
# leía: os.getenv() solo ve variables realmente exportadas al proceso.
load_dotenv()

# El modo debug de Werkzeug habilita un debugger interactivo que permite
# ejecutar código Python arbitrario desde el navegador si queda expuesto.
# Por eso NUNCA debe estar activo por defecto en un entorno real: se
# controla con la variable de entorno DASH_DEBUG (por defecto "false").
DEBUG_MODE = os.getenv("DASH_DEBUG", "false").strip().lower() == "true"

# Tamaño máximo de archivo aceptado (en bytes). Evita que un Excel muy
# grande bloquee el proceso (Dash corre en un solo hilo por defecto) o
# agote la memoria del servidor/navegador.
MAX_FILE_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Extensiones de archivo aceptadas por la UI de carga.
ALLOWED_UPLOAD_EXTENSIONS = (".xlsx", ".xls")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ca_li_analyzer")
