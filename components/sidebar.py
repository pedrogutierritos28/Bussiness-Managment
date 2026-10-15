"""
Componente sidebar.py
Este componente define la barra lateral de navegación de la aplicación.
Mostrará diferentes opciones de navegación según el rol del usuario (superadmin, admin, usuario, lector).
La barra lateral se renderiza en todas las páginas de la aplicación, excepto en la pantalla de login y en la pantalla de home,
(que es la primera pantalla después del login).
La barra lateral contiene enlaces a las siguientes vistas:
- Analizador: vista principal para crear y visualizar gráficas.
- Archivos compartidos: vista para acceder a archivos compartidos por otros usuarios.
- Administración: vista para administrar usuarios y permisos (solo para superadmin y admin).
- Graficas y reportes: vista para generar reportes automáticos (solo para superadmin, admin y usuario).
El componente utiliza Dash y Dash Iconify para renderizar los elementos de la barra lateral.

"""

from dash import html
from dash_iconify import DashIconify
from flask import session

def sidebar_layout():
    return html.Div(
        className="sidebar",
        children=[
            html.Div(
                className="sidebar-header",
                children=[
                    html.Div(
                        className="sidebar-brand-icon",
                        children="📊",
                    ),
                    html.H1(
                        "CA Y LI Analyzer",
                        className="sidebar-brand",
                    ),
                ],
            ),
            html.Div(
                className="sidebar-menu",
                children=[
                    crear_item_menu("Analizador", "chart-line", "analizador"),
                    crear_item_menu("Archivos compartidos", "folder-open", "compartidos"),
                    crear_item_menu("Administración", "user-cog", "administracion"),
                    crear_item_menu("Gráficas y reportes", "file-chart-line", "reportes"),
                    crear_item_menu("Cerrar sesión", "sign-out-alt", "logout"),
                ],
            ),
        ],
    )

def crear_item_menu(nombre, icono, vista):
    return html.Div(
        className="sidebar-menu-item",
        children=[
            DashIconify(icon=icono, width=20, height=20),
            html.Span(nombre, className="sidebar-menu-text"),
        ],
        id={"type": "nav-item", "index": vista},
        n_clicks=0,
    )

#funcion que lee session.get("role"), devuelve el rol del usuario logueado, o None si no hay usuario logueado
def obtener_rol_usuario():
    if not session:
        return None
    return session.get("role")