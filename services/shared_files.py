"""
Persistencia de archivos compartidos en Supabase (tabla `shared_files`).

Mientras `supabase_client.py` se encarga de la AUTENTICACIÓN (login y rol
del usuario), este módulo concentra las operaciones de DATOS sobre la
tabla `shared_files`: guardar, listar y recuperar archivos Excel que los
usuarios comparten entre sí.

Todas las operaciones usan el cliente admin (service_role key) de
`supabase_client.get_admin_client()`: la autorización por rol se valida
en los callbacks (`core/security.require_role`) ANTES de llegar aquí, así
que estas funciones asumen que quien las invoca ya está autorizado y no
dependen de políticas RLS.

Esquema esperado de la tabla `shared_files`:
    id, nombre_archivo, dataframe_json, analysis_json,
    uploaded_by (FK -> profiles.id), filas, columnas, fecha_creacion
"""


import logging

from services.supabase_client import get_admin_client

logger = logging.getLogger("ca_li_analyzer")

#Guardar un archivo compartido. Recibe: el dataframe convertido a JSON, el análisis (también JSON),
# el nombre del archivo, el id de quién lo subió, y cuántas filas/columnas tiene. Inserta una fila nueva en la tabla shared_files usando get_admin_client()

def save_shared_file(json_data, analysis, filename, user_id, num_rows, num_columns):
    try:
        client = get_admin_client()
        response = client.table("shared_files").insert({
            "nombre_archivo": filename,
            "dataframe_json": json_data,
            "analysis_json": analysis,
            "uploaded_by": user_id,
            "filas": num_rows,
            "columnas": num_columns
        }).execute()
        return {"success": True, "error": None}
    except Exception as e:
        logger.error("Error al guardar archivo compartido: %s", e)
        return {"success": False, "error": str(e)}

#Lista los archivos compartidos con columnas ligeras (sin el dataframe completo): 
#id, nombre, filas, columnas, fecha de creación y el nombre/correo de quien lo subió (join embebido a profiles). 
#Devuelve una lista de dicts ([] si falla la consulta); nunca lanza excepciones hacia quien la llama.

def list_shared_files():
    try:
        client = get_admin_client()
        #Lista de columnas ligeras
        response = client.table("shared_files").select("id, nombre_archivo, filas, columnas, fecha_creacion, profiles(nombre, correo)").execute()
        if response.data:
            return response.data
        else:
            return []
    except Exception as e:
        logger.error("Error al listar archivos compartidos: %s", e)
        return []

# Devuelve la fila completa de shared_files para el id dado
# (incluidos dataframe_json y analysis_json), o None si no existe o si la consulta falla.

def get_shared_file_by_id(file_id):
    try:
        client = get_admin_client()
        response = client.table("shared_files").select("*").eq("id", file_id).execute()
        if response.data:
            return response.data[0]
        else:
            return None
    except Exception as e:
        logger.error("Error al obtener archivo compartido por ID: %s", e)
        return None