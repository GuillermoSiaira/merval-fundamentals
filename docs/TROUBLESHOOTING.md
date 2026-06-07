# Troubleshooting — Merval Fundamentals

## Errores frecuentes

---

### `ALPHACAST_API_KEY no configurada`

**Síntoma:** `ValueError: Falta ALPHACAST_API_KEY`

**Solución:**
1. Ir a https://www.alphacast.io/settings/api-keys
2. Copiar la API key
3. En `.env`: `ALPHACAST_API_KEY=alphacast_TU_KEY`
4. En GCP: `gcloud functions deploy ... --set-env-vars="ALPHACAST_API_KEY=..."`

---

### MCP AlphaCast no responde

**Síntoma:** Timeout o `mcp_servers` error en Claude

**Solución:**
1. Verificar que el MCP está instalado en `claude_desktop_config.json`
2. Reiniciar Claude Desktop
3. Probar manualmente: `curl -H "Authorization: Bearer TU_KEY" https://mcp.alphacast.io/health`
4. Si el servicio está caído, AlphaCast envía status a hello@alphacast.io

---

### Telegram error 400 Bad Request

**Síntoma:** `Telegram error 400: can't parse entities`

**Causa:** El mensaje tiene caracteres especiales no escapados en MarkdownV2

**Solución:**
El `TelegramNotifier` hace retry automático sin `parse_mode`. Si persiste:
```python
notifier.send_message(text, parse_mode="")  # sin formato
```

---

### Telegram `chat not found`

**Síntoma:** `{"ok":false,"description":"chat not found"}`

**Causa:** El bot no tiene acceso al chat o el `CHAT_ID` es incorrecto

**Solución:**
1. El bot debe haber sido agregado al grupo/chat
2. El bot debe haber recibido al menos un mensaje en ese chat
3. Verificar CHAT_ID: `https://api.telegram.org/bot{TOKEN}/getUpdates`

---

### GCP Cloud Function timeout

**Síntoma:** `Deadline exceeded` en Cloud Logging

**Causa:** AlphaCast tarda demasiado para 20 tickers secuencialmente

**Solución:**
- El timeout está en 300s (suficiente para 20 tickers)
- Si persiste, reducir el panel a 10 tickers en `PANEL_LIDER`
- Considerar paralelizar con `asyncio` en una versión futura

---

### `pytest` falla con `ModuleNotFoundError: src`

**Síntoma:** `ModuleNotFoundError: No module named 'src'`

**Solución:**
```powershell
# Desde la raíz del proyecto
cd D:\projects\merval-fundamentals
.\venv\Scripts\Activate.ps1
pytest tests/ -v  # debe correr desde la raíz
```

Si persiste, agregar al inicio de los tests:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

---

### Firestore `PERMISSION_DENIED`

**Síntoma:** `google.api_core.exceptions.PermissionDenied`

**Causa:** El service account no tiene rol Firestore Admin

**Solución:**
1. GCP Console → IAM & Admin → Service Accounts
2. Seleccionar `merval-fundamentals-sa`
3. Agregar rol `Cloud Datastore User` (o `Firestore Admin`)

---

### GitHub Actions deploy falla con `INVALID_ARGUMENT`

**Síntoma:** `ERROR: (gcloud.functions.deploy) INVALID_ARGUMENT`

**Causa:** Generalmente un `requirements.txt` mal formado en `gcp/`

**Solución:**
```bash
# Verificar localmente
cd gcp
pip install -r requirements.txt
```

---

### Datos incoherentes de AlphaCast

**Síntoma:** ROE > 2.0 o P/BV > 20

**Causa:** AlphaCast devolvió datos erróneos o de un ticker incorrecto

**Solución:**
El `AlphaCastClient.validate_data()` filtra automáticamente estos casos.
Para debug:
```python
client = AlphaCastClient()
data = client.get_ticker_data("GGAL")
print(client.validate_data(data))  # True si OK
```

---

## Contactos

| Servicio | Soporte |
|----------|---------|
| AlphaCast | hello@alphacast.io |
| GCP | https://cloud.google.com/support |
| Telegram BotFather | @BotFather |
| Repositorio | https://github.com/GuillermoSiaira/merval-fundamentals/issues |
