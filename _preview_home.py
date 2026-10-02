"""
Preview TEMPORAL de la pantalla Home (components/home.py).

La app real todavía no conecta el home (eso llega con la Fase 1, cuando
exista el shell con sidebar y el callback de navegación). Este script
levanta una mini-app Dash cuyo layout es ÚNICAMENTE el home, para poder
revisarlo visualmente por rol:

    .\\venv\\Scripts\\python.exe _preview_home.py admin
    .\\venv\\Scripts\\python.exe _preview_home.py usuario
    .\\venv\\Scripts\\python.exe _preview_home.py lector

Luego abre http://127.0.0.1:8052 en el navegador.

NOTAS:
- Los botones de navegación no hacen nada aquí (no hay callback de
  navegación en esta mini-app); solo se revisa el aspecto visual.
- Borrar este archivo cuando el home quede conectado en la app real.
"""

import sys

from dash import Dash

from components.home import home_layout


ROL = sys.argv[1] if len(sys.argv) > 1 else "admin"

app = Dash(
    __name__,
    title=f"Preview Home — rol: {ROL}",
)

app.layout = home_layout(ROL)

if __name__ == "__main__":
    print(f"Preview del home para rol '{ROL}' -> http://127.0.0.1:8052")
    app.run(debug=False, port=8052)
