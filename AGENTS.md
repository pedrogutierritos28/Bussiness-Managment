# AGENTS.md — CA Y LI Analyzer

Guía para agentes de IA que trabajen en este proyecto. Léela completa antes
de modificar código: contiene decisiones de diseño y trampas conocidas que
no son evidentes leyendo los archivos por separado.

## ¿Qué es este proyecto?

Aplicación web **Dash (Python/Flask)** para analizar archivos Excel:
el usuario inicia sesión (Supabase Auth), sube un `.xlsx`/`.xls`, la app
detecta tipos de columnas y calidad de datos, y permite generar gráficas
(Plotly) y exportar CSV/PNG/reporte de calidad.

## Comandos (Windows)

El `python` global NO tiene las dependencias. Usa siempre el venv:

```powershell
.\venv\Scripts\python.exe app.py                    # correr la app
.\venv\Scripts\python.exe -m pytest tests -q        # correr tests
```

## Variables de entorno (.env)

Requeridas en producción; sin ellas la app arranca con degradaciones
controladas (SECRET_KEY temporal, login sin funcionar):

- `SUPABASE_URL`, `SUPABASE_ANON_KEY` — login contra Supabase Auth.
- `SUPABASE_SERVICE_ROLE_KEY` — solo server-side, para leer `public.profiles`
  (rol del usuario). NUNCA mandarla al navegador.
- `SECRET_KEY` — firma de la cookie de sesión de Flask.
- `DASH_DEBUG` ("true"/"false"), `MAX_UPLOAD_SIZE_MB` (default 20).

## Estructura

```
app.py                  Punto de entrada MÍNIMO: layout raíz, re-exports,
                        __main__. NO agregar lógica aquí (ver "Trampas").
config.py               Constantes del entorno (DEBUG_MODE, límites) y logger
                        "ca_li_analyzer"
app_instance.py         Instancia Dash + SECRET_KEY + singletons
                        (analyzer, chart_generator). Existe para romper
                        imports circulares: los callbacks importan de aquí.
core/
  security.py           is_authenticated, require_session, require_role
  helpers.py            user_facing_error, restore_column_types
components/
  login.py              Layout de la pantalla de login
  analyzer.py           Layout del analizador (vista principal)
  notifications.py      make_toast(): construcción de notificaciones toast
callbacks/              Cada módulo registra sus callbacks con @app.callback
                        al ser importado; callbacks/__init__.py los importa
  auth.py               authenticate, logout
  upload.py             process_excel (+ _UploadState, _empty_upload_state)
  chart_controls.py     update_chart_types, update_advanced_controls
  chart.py              generate_chart
  exports.py            export_csv, export_png, export_report
  notifications.py      Toasts: callbacks "espejo" que observan los mensajes
                        inline (file-status/chart-message/export-message) y
                        los replican como toast vía dcc.Store("toast-inbox").
services/               Lógica de negocio pura (sin Dash):
  excel_analyzer.py     Detección de tipos, estadísticas, identificadores
  chart_generator.py    Generación de figuras Plotly
  supabase_client.py    Autenticación: sign_in + lectura de rol desde
                        public.profiles (cliente admin)
  shared_files.py       Persistencia de archivos compartidos (tabla
                        shared_files): save/list/get_by_id. La autorización
                        por rol se valida ANTES, en los callbacks, con
                        require_role(); estas funciones asumen llamador
                        ya autorizado.
  normalization.py      Normalización de texto
utils/                  Utilidades varias
tests/                  Suite pytest (invoca callbacks directamente)
assets/style.css        Estilos (Dash los sirve automáticamente)
```

Regla de capas: la lógica de negocio va en `services/`; los callbacks en
`callbacks/` solo orquestan (validan sesión, llaman servicios, arman UI).

## Convenciones

- Código, comentarios, docstrings y mensajes de UI en **español**.
- Errores al usuario SIEMPRE vía `user_facing_error()` (mensaje genérico en
  UI + detalle técnico solo en el log). Nunca exponer trazas, rutas, ni
  nombres de librerías al usuario.
- Callbacks protegidos llaman `require_session()` (u `require_role()`)
  como PRIMERA línea; `abort()` (no `return`) para rechazar peticiones.
- Mensajes de UI con clases CSS existentes: `error-message`,
  `warning-message`, `success-message`.

## Decisiones de diseño que NO deben "simplificarse"

1. **El rol se lee con el service_role key** (`get_admin_client()` en
   `services/supabase_client.py`), no con el cliente de la anon key: el
   cliente anon es singleton `@lru_cache` cuyo estado de sesión se pisaría
   entre logins concurrentes, y dependería de políticas RLS. No "arreglarlo".
2. **`require_role()` existe pero AÚN NO se aplica a ningún callback** a
   propósito (trabajo por fases). No es un olvido.
3. **Guards contra el "disparo fantasma" de Dash** en `authenticate`/`logout`
   (`if not n_clicks: raise PreventUpdate`): impiden que remontar el botón
   dispare el callback y cierre la sesión recién creada. NO quitarlos.
4. **El mock de los tests depende de las re-exportaciones de `app.py`**
   (`process_excel`, `authenticate`, `supabase_client`, etc.). Si se quitan,
   `tests/test_app_callbacks.py` se rompe aunque la app funcione. Si se
   mueve una función, hay que mantener el re-export o actualizar el target
   del monkeypatch (ej. `callbacks.upload.MAX_FILE_SIZE_BYTES`).
5. **Los toasts se emiten con callbacks "espejo"**, no agregando Outputs a
   los callbacks existentes (eso rompería el unpacking por tuplas en los
   tests). El login fallido NO genera toast (solo mensaje inline) por
   decisión del usuario.

## Trampas conocidas

- `tests/test_app_callbacks.py::test_export_png_failure_does_not_leak_technical_details`
  **falla cuando kaleido ESTÁ instalado** en el entorno (el test asume que
  la exportación PNG falla). Es preexistente conocido; el resto de la suite
  debe quedar en verde (87 passed).
- Estado de referencia de la suite al actualizar este archivo:
  **99 passed, 1 failed (el de kaleido)**.
- No hacer commits ni push sin permiso explícito del usuario.
