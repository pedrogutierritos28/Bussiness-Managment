"""
Cliente de Supabase para autenticación de usuarios.

Este módulo NO implementa persistencia de datos de la app (eso vive en
`shared_files.py`); resuelve el inicio de sesión contra Supabase Auth y,
tras autenticar, lee el rol del usuario desde la tabla `profiles`
(columna `rol`: 'superadmin', 'admin', 'usuario', 'lector') que deciden
qué puede hacer en la app (ver require_role en app.py).
"""

import logging
import os
from functools import lru_cache

from supabase import create_client, Client

logger = logging.getLogger("ca_li_analyzer")


@lru_cache(maxsize=1)
def get_client() -> Client:
    """
    Crea el cliente de Supabase una sola vez (cacheado) usando
    SUPABASE_URL / SUPABASE_ANON_KEY del entorno.

    Lanza RuntimeError con un mensaje claro si faltan las variables,
    en vez de dejar que falle más adelante con un error críptico de
    la librería.
    """

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError(
            "Faltan SUPABASE_URL / SUPABASE_ANON_KEY en las variables de "
            "entorno (.env). El login no puede validar credenciales sin "
            "ellas."
        )

    return create_client(url, key)


@lru_cache(maxsize=1)
def get_admin_client() -> Client:
    """
    Cliente de Supabase con la service_role key: puede leer cualquier
    fila sin depender de políticas RLS (que hoy pueden no existir o no
    cubrir este caso).

    Se usa específicamente para leer el rol del usuario justo después
    del login. Es importante NO reutilizar el cliente `get_client()`
    (el de la anon key) para esto: ese cliente es un singleton
    compartido por todo el proceso (@lru_cache), y su estado de sesión
    interno (qué usuario quedó autenticado tras sign_in_with_password)
    puede pisarse entre logins concurrentes de distintos usuarios. El
    cliente admin, en cambio, nunca "inicia sesión como" nadie -- cada
    consulta es independiente y no depende de estado compartido.
    """

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise RuntimeError(
            "Faltan SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY en las "
            "variables de entorno (.env)."
        )

    return create_client(url, key)


def sign_in(email: str, password: str) -> dict:
    """
    Intenta iniciar sesión contra Supabase Auth.

    Devuelve siempre un dict con esta forma, sin lanzar excepciones
    hacia quien llama (cualquier error de red, configuración faltante,
    o credenciales inválidas se traduce a success=False):

        {"success": bool, "user": {"id": str, "email": str} | None,
         "error": str | None}

    El campo "error" es para logging interno; el callback que use esta
    función NO debe mostrárselo tal cual al usuario (evita filtrar
    detalles técnicos de Supabase en la UI).
    """

    if not email or not password:
        return {
            "success": False,
            "user": None,
            "error": "Correo o contraseña vacíos",
        }

    try:
        client = get_client()

        result = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

    except Exception as error:
        return {
            "success": False,
            "user": None,
            "error": str(error),
        }

    if not result or not result.user:
        return {
            "success": False,
            "user": None,
            "error": "Supabase no devolvió un usuario válido",
        }

    # El rol se lee de la tabla profiles (columna rol) usando el cliente
    # con la service_role key -- NO el cliente recién autenticado -- para
    # no depender de políticas RLS todavía inexistentes y para no
    # compartir estado de sesión entre logins concurrentes de distintos
    # usuarios (ver docstring de get_admin_client). Si la consulta falla
    # (tabla ausente, fila inexistente, llave faltante), se usa 'usuario'
    # por defecto para no bloquear el acceso; el detalle queda en el log.
    rol = "usuario"

    try:
        perfil = (
            get_admin_client()
            .table("profiles")
            .select("rol")
            .eq("id", result.user.id)
            .limit(1)
            .execute()
        )

        rows = getattr(perfil, "data", None) or []

        if rows and rows[0].get("rol"):
            rol = rows[0]["rol"]
        else:
            logger.warning(
                "El usuario %s no tiene fila en public.profiles (o no "
                "tiene 'rol'); se asume rol 'usuario'.",
                result.user.id,
            )

    except Exception as profile_error:
        logger.warning(
            "No se pudo leer el rol de profiles para %s: %s",
            result.user.email,
            profile_error,
        )

    return {
        "success": True,
        "user": {
            "id": result.user.id,
            "email": result.user.email,
        },
        "rol": rol,
        "error": None,
    }
