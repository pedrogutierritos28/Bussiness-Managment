"""
Paquete de callbacks de la aplicación Dash.

Los decoradores `@app.callback` se ejecutan al IMPORTAR cada módulo, así
que importarlos aquí es lo que registra todos los callbacks en la app.
`app.py` solo necesita `import callbacks` (o importar nombres desde este
paquete) para que el registro ocurra.
"""

from callbacks import (  # noqa: F401
    auth,
    chart,
    chart_controls,
    exports,
    notifications,
    upload,
)
