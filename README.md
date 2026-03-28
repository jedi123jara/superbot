# 🏦 Alpaca Backtest Bot — Koyeb

Bot de backtesting profesional sin martingala, deployable en [Koyeb](https://koyeb.com).

---

## 📁 Estructura esperada del proyecto

```
tu-proyecto/
├── main.py               ← FastAPI + endpoints
├── bot.py                ← Lógica del backtest
├── requirements.txt
├── Dockerfile
├── Procfile
├── .env.example
├── config/
│   └── settings.py       ← Tu módulo original
├── indicators/
│   └── calculator.py     ← Tu módulo original
└── backtest/
    └── simulator.py      ← Tu módulo original
```

> ⚠️ Los módulos `config`, `indicators` y `backtest` son los tuyos — no se modificaron.

---

## 🚀 Deploy en Koyeb

### Opción A — GitHub (recomendado)

1. Sube el proyecto a un repositorio de GitHub
2. En Koyeb → **Create Service** → **GitHub**
3. Selecciona el repo y la rama
4. Koyeb detecta el `Dockerfile` automáticamente
5. Agrega las variables de entorno (ver abajo)
6. Click en **Deploy**

### Opción B — Docker directo

```bash
docker build -t alpaca-bot .
docker run -p 8000:8000 --env-file .env alpaca-bot
```

---

## 🔑 Variables de entorno en Koyeb

Ve a **Settings → Environment Variables** y agrega:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `ALPACA_API_KEY` | Tu API Key de Alpaca | `PK...` |
| `ALPACA_SECRET_KEY` | Tu Secret Key de Alpaca | `...` |
| `ALPACA_BASE_URL` | URL base (paper o live) | `https://paper-api.alpaca.markets` |
| `AUTO_RUN` | Ejecutar al iniciar | `false` |
| `CAPITAL_INICIAL` | Capital inicial en USD | `1000.0` |
| `RIESGO_PCT` | % de riesgo por trade | `0.10` |
| `TAKE_PROFIT_PCT` | Take profit % | `0.03` |
| `STOP_LOSS_PCT` | Stop loss % | `0.003` |
| `DIAS_HISTORICO` | Días de histórico | `365` |

---

## 🌐 Endpoints disponibles

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Health check + estado del bot |
| `GET` | `/health` | Health check simple (usado por Koyeb) |
| `POST` | `/run` | ▶️ Iniciar el backtest manualmente |
| `GET` | `/status` | Ver estado y último resultado |
| `DELETE` | `/reset` | Resetear estado del bot |

### Ejemplo — iniciar el backtest:
```bash
curl -X POST https://tu-servicio.koyeb.app/run
```

### Ejemplo — ver resultados:
```bash
curl https://tu-servicio.koyeb.app/status
```

**Respuesta `/status` cuando termina:**
```json
{
  "status": "completed",
  "last_result": {
    "capital_inicial": 1000.0,
    "capital_final": 1243.87,
    "retorno_pct": 24.39,
    "win_rate_pct": 67.5,
    "total_trades": 480,
    "ganadores": 324,
    "perdedores": 156
  }
}
```

---

## ⚙️ Health Check en Koyeb

Koyeb necesita un endpoint de salud. Configúralo así:

- **Path:** `/health`
- **Port:** `8000`
- **Protocol:** `HTTP`

---

## 📝 Notas

- El backtest corre en un **thread separado** para no bloquear el servidor
- Si `AUTO_RUN=true`, el backtest inicia automáticamente al desplegar
- Los logs se ven en tiempo real en **Koyeb → Logs**
- Para producción cambia `ALPACA_BASE_URL` a `https://api.alpaca.markets`
