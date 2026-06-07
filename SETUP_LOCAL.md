# SETUP_LOCAL.md — Setup local de Merval Fundamentals

Documenta los pasos ejecutados para dejar el repo listo para desarrollo local y
para Cowork. Generado el 2026-06-07.

Entorno: Windows 10 · PowerShell · Python 3.13.2 · venv en `.\venv`

---

## 1. Estado del repo verificado

- `git status` limpio sobre `main`.
- `src/` contiene 4 módulos + `__init__.py`.
- `tests/` contiene 3 suites + `__init__.py`.
- Ya existían `.env`, `.env.example`, `requirements.txt`, `setup.py`,
  `.github/workflows/` (tests.yml + deploy.yml), `gcp/`, `cowork/`, `docs/`.

---

## 2. Variables de entorno (`.env`)

`.env` está en `.gitignore` (no se commitea). Se cargaron valores mínimos como
**sentinelas** para indicar qué falta completar en Cowork:

```env
ALPHACAST_API_KEY=required_in_cowork
TELEGRAM_BOT_TOKEN=required_in_cowork
TELEGRAM_CHAT_ID=required_in_cowork
GOOGLE_APPLICATION_CREDENTIALS=C:\gcp\abu-oracle-sa.json
```

> `.env.example` mantiene el template original con el formato de cada valor.

---

## 3. Virtualenv

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

El venv ya estaba creado con todas las dependencias instaladas
(`anthropic 0.107`, `pandas 3.0`, `google-cloud-firestore`, `pytest 9`, etc.).

---

## 4. Validación de módulos

Todos los módulos de `src/` importan sin errores:

```powershell
.\venv\Scripts\python.exe -c "import src.alphacast_client, src.analyzer, src.report_generator, src.telegram_notifier; print('OK')"
```

### Funciones / clases principales

| Módulo | Clase principal | Métodos clave |
|--------|-----------------|----------------|
| `alphacast_client.py` | `AlphaCastClient` | `get_ticker_data`, `get_panel_data`, `validate_data`, `_fetch_via_mcp`, `_simulate` |
| `analyzer.py` | `FundamentalAnalyzer` | `from_dict`, `signal`, `score`, `rank`, `rationale`, `generate_report` |
| `report_generator.py` | `ReportGenerator` | `telegram_message`, `html_report` |
| `telegram_notifier.py` | `TelegramNotifier` | `test_connection`, `send_message`, `send_document`, `send_error` |

Constante exportada: `PANEL_LIDER` (20 tickers) y `SECTOR_MAP` en `alphacast_client.py`.

### ⚠️ Correcciones aplicadas (archivos venían truncados en el commit inicial)

Dos archivos estaban cortados a mitad de sentencia y rompían la importación /
colección de tests. Se completaron:

- **`src/alphacast_client.py`** — el `return {...}` de `_simulate()` estaba
  cortado en `**`. Se cerró con `**d,` + `}` para devolver el dict simulado completo.
- **`tests/test_telegram.py`** — terminaba en un decorador `@patch("requests.get")`
  colgado. Se completó con `test_connection_test_fails` (verifica que
  `test_connection()` devuelve `False` ante una excepción de red).

---

## 5. Tests

Suite completa (modo simulación, sin credenciales):

```powershell
.\venv\Scripts\python.exe -m pytest tests/ -m "not live" --cov=src --cov-report=term-missing --cov-fail-under=70
```

Resultado: **43 passed, 3 deselected** · cobertura **74%** (umbral CI: 70%).

Los 3 tests deseleccionados son `@pytest.mark.live` (requieren
`ALPHACAST_API_KEY` real). El marcador `live` se registró en `pytest.ini`.

---

## 6. GitHub Actions

Ya existían los workflows; se corrigió un problema de cobertura:

- **`.github/workflows/tests.yml`** y **`deploy.yml`** corrían solo
  `test_analyzer.py + test_telegram.py`, lo que dejaba `alphacast_client.py` en 0%
  y la cobertura total en 59% → el gate `--cov-fail-under=70` **fallaba**.
- Se cambió el comando a `pytest tests/` (corre las 3 suites; las live siguen
  excluidas por `-m "not live"`, no requieren secretos). Cobertura → 74%. ✅
- Se agregó `pytest.ini` registrando el marcador `live`.

---

## 7. Qué falta (para Cowork / producción)

- **Secretos en Cowork / GCP**: completar los `required_in_cowork` del `.env`
  y cargar en GCP Secrets / GitHub Secrets:
  `ALPHACAST_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GCP_SA_KEY`.
- **Credenciales GCP**: colocar el service-account JSON en
  `C:\gcp\abu-oracle-sa.json` (ruta de `GOOGLE_APPLICATION_CREDENTIALS`).
- **Deploy GCP (revisar antes de usar)**: `deploy.yml` usa `--source=.` con
  `--entry-point=merval_analysis`, pero la función vive en
  `gcp/cloud_function.py` y la `requirements.txt` raíz **no** incluye
  `functions-framework`. Cloud Functions espera el entry point en `main.py` en
  la raíz del source. Antes del primer deploy hay que: usar `--source=gcp` (con
  `gcp/requirements.txt`, que sí tiene `functions-framework`) **o** crear un
  `main.py` raíz que re-exporte `merval_analysis`.
- **MCP AlphaCast**: debe estar instalado/configurado en el entorno que ejecute
  el pipeline real (ver README).

---

## Comandos rápidos

```powershell
# Activar venv
.\venv\Scripts\Activate.ps1

# Correr tests como en CI
.\venv\Scripts\python.exe -m pytest tests/ -m "not live" --cov=src

# Smoke test del pipeline (modo simulación)
.\venv\Scripts\python.exe -m src.analyzer
```
