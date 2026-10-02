"""
Pantalla de inicio ("home") mostrada justo después de iniciar sesión.

En vez de aventar al usuario directo al analizador con todos sus controles
a la vista, esta pantalla pregunta primero QUÉ quiere hacer, mediante
tarjetas de acción, y solo entonces navega a la vista correspondiente.
Reduce la carga cognitiva inicial y da un lugar natural para ubicar
funciones futuras sin seguir amontonando todo en una sola pantalla larga.

Tarjetas y su estado actual:
    - "Crear gráfica"      -> FUNCIONAL, navega a la vista del analizador.
    - "Agregar usuario"    -> Solo visual ("Próximamente"). Panel de
                              administración aún no construido.
    - "Editar celdas"      -> Solo visual ("Próximamente"). Feature nueva,
                              pendiente de planear (permisos de edición,
                              si afecta el archivo compartido o es local).
    - "Reporte automático" -> Solo visual ("Próximamente"). Feature nueva,
                              pendiente de planear (llamada a la API de
                              Claude, control de costos).

Visibilidad por rol (usa session["role"], mismo patrón que require_role
en core/security.py -- NO dupliques esta lógica en otro lado):
    - superadmin / admin: ve las 4 tarjetas.
    - usuario: ve "Crear gráfica", "Editar celdas" y "Reporte automático";
      NO ve "Agregar usuario" (esa tarjeta es exclusiva de admin+).
    - lector: NO ve ninguna de las 4 tarjetas -- esta pantalla le muestra
      en su lugar un mensaje simple con un acceso hacia "Archivos
      compartidos" (aunque esa sección todavía no esté construida).
    - Rol desconocido/None: mensaje genérico SIN accesos de navegación,
      porque no se puede asumir qué permisos tendría esa cuenta.

Navegación (sin URLs):
    Las tarjetas funcionales NO son dcc.Link: la app no tiene dcc.Location
    ni rutas, así que un href provocaría una recarga completa y devolvería
    al usuario a la pantalla de login. En su lugar son html.Button con ids
    de patrón {"type": "nav-item", "index": <vista>} -- el MISMO patrón
    que usará la barra lateral (Fase 1) —, consumidos por el callback de
    navegación en callbacks/navigation.py. Las tarjetas "Próximamente"
    son botones disabled sin id de navegación: no pueden disparar nada.

Esta pantalla vive DESPUÉS del login y ANTES de app_instance/analyzer:
no reemplaza a components/analyzer.py, solo decide a cuál vista navegar.
"""

from dash import html
from dash_iconify import DashIconify


def home_layout(user_role):
    # Normalizar el rol: neutraliza None, mayúsculas y espacios que
    # pudiera traer de la base de datos antes de comparar.
    user_role = (user_role or "").strip().lower()

    if user_role in ("superadmin", "admin"):
        tarjetas = [
            crear_tarjeta("Crear gráfica", "chart-line", vista="analizador"),
            crear_tarjeta("Agregar usuario", "user-plus", proximo=True),
            crear_tarjeta("Editar celdas", "edit", proximo=True),
            crear_tarjeta("Reporte automático", "file-chart-line", proximo=True),
        ]

    elif user_role == "usuario":
        tarjetas = [
            crear_tarjeta("Crear gráfica", "chart-line", vista="analizador"),
            crear_tarjeta("Editar celdas", "edit", proximo=True),
            crear_tarjeta("Reporte automático", "file-chart-line", proximo=True),
        ]

    elif user_role == "lector":
        return html.Div(
            className="home-container",
            children=[
                html.Div(
                    className="home-message",
                    children=[
                        html.H2("Bienvenido, lector"),
                        html.P(
                            "Actualmente no tienes permisos para realizar "
                            "acciones. Por favor, contacta a un "
                            "administrador."
                        ),
                        html.Button(
                            "Ir a Archivos compartidos",
                            id={"type": "nav-item", "index": "compartidos"},
                            className="home-inline-link",
                            n_clicks=0,
                        ),
                    ],
                )
            ],
        )

    else:
        # Rol desconocido o vacío: mensaje genérico, sin accesos de
        # navegación (no se puede asumir qué permisos tendría).
        return html.Div(
            className="home-container",
            children=[
                html.Div(
                    className="home-message",
                    children=[
                        html.H2("Bienvenido"),
                        html.P(
                            "Tu cuenta no tiene un rol reconocido. "
                            "Por favor, contacta a un administrador."
                        ),
                    ],
                )
            ],
        )

    return html.Div(
        className="home-container",
        children=[
            html.Div(
                className="home-grid",
                children=tarjetas,
            )
        ],
    )


def crear_tarjeta(titulo, icono, vista=None, proximo=False):
    """
    Construye una tarjeta de acción del home.

    - `vista` (funcional): botón con id de patrón {"type": "nav-item",
      "index": vista} para el callback de navegación.
    - `proximo` (visual): botón deshabilitado con etiqueta "Próximamente",
      SIN id de navegación — no puede disparar nada.
    """

    contenido = [
        DashIconify(icon=icono, width=50, height=50),
        html.H3(titulo)
    ]

    if proximo:
        contenido.append(html.P("Próximamente", className="proximo"))

        return html.Button(
            contenido,
            className="home-card",
            disabled=True,
        )

    return html.Button(
        contenido,
        id={"type": "nav-item", "index": vista},
        className="home-card",
        n_clicks=0,
    )
