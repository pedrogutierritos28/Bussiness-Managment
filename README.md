# CA Y LI Analyzer

Aplicación web para **analizar archivos Excel** de forma inteligente: con
inicio de sesión, detección automática de tipos de datos, métricas de
calidad, generación de gráficas interactivas y exportación de resultados.

## ¿Qué hace?

- 🔐 **Autenticación con roles** (Supabase Auth): superadmin, admin,
  usuario, lector. La sesión vive del lado del servidor (cookie firmada).
- 📂 **Carga de archivos Excel** (`.xlsx` / `.xls`) con validación de
  formato, tamaño máximo configurable y manejo de columnas duplicadas.
- 🔍 **Análisis automático**: detección de tipos de datos (numéricas,
  fechas, categóricas, texto, booleanas), estadísticas descriptivas y
  detección de identificadores/folios (numéricos y alfanuméricos).
- 📈 **Gráficas interactivas** (Plotly): barras, líneas temporales con
  periodo configurable, dispersión, histogramas, pie y boxplot.
- ⬇️ **Exportaciones**: CSV de datos, PNG de la gráfica y reporte de
  calidad de datos.
- 🔔 **Notificaciones toast**: avisos emergentes de éxito, advertencia y
  error con cierre automático o manual.
- 📁 **Archivos compartidos**: persistencia en Supabase para compartir
  análisis entre usuarios (con autorización por rol).

## Stack técnico

- **Backend/UI**: Python + [Dash](https://dash.plotly.com/) (sobre Flask) + Plotly
- **Datos**: pandas, openpyxl
- **Autenticación y persistencia**: [Supabase](https://supabase.com/)
- **Pruebas**: pytest (suite que invoca los callbacks directamente, sin
  navegador)

## Estructura del proyecto

```
app.py                  Punto de entrada
config.py               Constantes del entorno y logger
app_instance.py         Instancia Dash + SECRET_KEY + singletons
core/
  security.py           Autenticación y autorización (require_session, require_role)
  helpers.py            Errores amigables y utilidades de DataFrame
components/             Layouts y notificaciones (login, analyzer, toasts)
callbacks/              Callbacks de Dash (auth, upload, chart, exports, notifications)
services/               Lógica de negocio (análisis, gráficas, Supabase, compartidos)
tests/                  Suite pytest
assets/style.css        Estilos
```

## Requisitos

- Python 3.11+ (probado en Windows, compatible multiplataforma)
- Un proyecto de [Supabase](https://supabase.com/) con:
  - Autenticación por email/contraseña habilitada
  - Tabla `public.profiles` con columna `rol` (por usuario)
  - Tabla `public.shared_files` (para archivos compartidos)

## Instalación

```powershell
# 1. Clonar el repositorio
git clone https://github.com/pedrogutierritos28/Bussiness-Managment.git
cd Bussiness-Managment

# 2. Crear y activar el entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
#    Copia .env.example a .env y completa tus llaves de Supabase
Copy-Item .env.example .env
```

### Variables de entorno (`.env`)

| Variable | Descripción |
|---|---|
| `SUPABASE_URL` | URL de tu proyecto Supabase |
| `SUPABASE_ANON_KEY` | Llave pública (anon key) |
| `SUPABASE_SERVICE_ROLE_KEY` | Llave secreta, **solo servidor**. Nunca la compartas ni la expongas al navegador |
| `SECRET_KEY` | Cadena aleatoria larga para firmar cookies de sesión |
| `DASH_DEBUG` | `true`/`false` (por defecto `false`; nunca `true` en producción) |
| `MAX_UPLOAD_SIZE_MB` | Tamaño máximo de archivo Excel (por defecto 20) |

## Uso

```powershell
.\venv\Scripts\python.exe app.py
```

Abre http://127.0.0.1:8050 en tu navegador, inicia sesión y sube un archivo
Excel para empezar a analizarlo.

## Pruebas

```powershell
.\venv\Scripts\python.exe -m pytest tests -q
```

La suite cubre el análisis de Excel, la generación de gráficas, los
callbacks de la app (carga, exportaciones, autenticación, toasts) y el
cliente de Supabase — todo con mocks, sin llamadas de red reales.

## Seguridad

- Las credenciales y llaves viven **solo** en `.env` (ignorado por git).
- Los callbacks sensibles verifican sesión (`require_session`) y rol
  (`require_role`) del lado del servidor antes de procesar nada.
- Los errores mostrados al usuario son genéricos; el detalle técnico solo
  se registra en el log del servidor.

## Contribuir

1. Crea una rama desde `main`
2. Haz tus cambios y verifica que la suite de tests siga en verde
3. Abre un Pull Request describiendo el cambio

Para colaboradores que usen asistentes de IA, el repositorio incluye
`AGENTS.md` con el contexto de arquitectura, convenciones y decisiones de
diseño del proyecto.
