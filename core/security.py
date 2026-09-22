"""
Guardas de seguridad para los callbacks de Dash.

`require_session()` y `require_role()` se llaman al inicio de cada
callback sensible para rechazar peticiones sin sesión válida (401) o sin
el rol necesario (403) ANTES de procesar nada.
"""

from flask import abort, session

from config import logger


def is_authenticated() -> bool:
    """
    True si la petición actual trae una cookie de sesión válida creada
    por un login exitoso (ver callback `authenticate`).
    """

    return bool(session.get("authenticated"))


def require_session() -> None:
    """
    Corta la ejecución de un callback con un 401 si no hay sesión
    autenticada. Se llama al inicio de cada callback que lee, genera o
    exporta datos del Excel cargado.

    Se usa `abort()` (no un simple `return`) a propósito: así el
    servidor rechaza la petición HTTP en sí, en vez de devolver una
    respuesta 200 "vacía" que igual confirmaría que el callback existe
    y procesó algo.
    """

    if not is_authenticated():
        logger.warning(
            "Intento de acceso a un callback protegido sin sesión válida."
        )
        abort(401)


def require_role(*roles_permitidos: str) -> None:
    """
    Igual que `require_session()`, pero además exige que el rol del
    usuario (guardado en `session["role"]` durante el login, a partir
    de la columna `rol` de la tabla public.profiles) esté dentro de
    `roles_permitidos`.

    - Sin sesión autenticada -> 401 (igual que require_session()).
    - Sesión con un rol no permitido -> 403.

    El 403 comunica algo distinto al 401: "sé quién eres, pero tu rol
    no te autoriza a hacer esto". Como con require_session(), se usa
    `abort()` para rechazar la petición HTTP completa en vez de
    devolver una respuesta 200 vacía.
    """

    if not is_authenticated():
        logger.warning(
            "Intento de acceso a un callback protegido sin sesión válida."
        )
        abort(401)

    rol = session.get("role")

    if rol not in roles_permitidos:
        logger.warning(
            "Acceso denegado (403): rol %r no está en %s.",
            rol,
            roles_permitidos,
        )
        abort(403)
