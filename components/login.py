from datetime import datetime
from dash import html, dcc


def obtener_saludo():
    hora = datetime.now().hour

    if 5 <= hora < 12:
        return "Buenos días"
    elif 12 <= hora < 19:
        return "Buenas tardes"
    else:
        return "Buenas noches"


def login_layout():
    saludo = obtener_saludo()

    return html.Div(
        className="login-container",
        children=[
            html.Div(
                className="login-card",
                children=[
                    html.Div(
                        className="login-brand-icon",
                        children="📊",
                    ),
                    html.H1(
                        "CA Y LI Analyzer",
                        className="login-brand",
                    ),
                    html.H2(
                        f"{saludo}",
                        className="login-title",
                    ),
                    html.P(
                        "Inicia sesión para acceder al sistema",
                        className="login-subtitle",
                    ),
                    html.Div(
                        className="login-field",
                        children=[
                            html.Label(
                                "Correo electrónico",
                                className="login-label",
                            ),
                            dcc.Input(
                                id="login-email",
                                type="email",
                                placeholder="correo@empresa.com",
                                className="login-input",
                            ),
                        ],
                    ),
                    html.Div(
                        className="login-field",
                        children=[
                            html.Label(
                                "Contraseña",
                                className="login-label",
                            ),
                            dcc.Input(
                                id="login-password",
                                type="password",
                                placeholder="Contraseña",
                                className="login-input",
                            ),
                        ],
                    ),
                    html.Button(
                        "Iniciar sesión",
                        id="login-button",
                        className="login-button",
                    ),
                    html.Div(
                        id="login-message",
                        className="login-message",
                    ),
                ],
            ),
        ],
    )